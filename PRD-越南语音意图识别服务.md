# PRD：越南语音 → 中文意图识别（Vie2Sort）

## 1. 背景与目标

实现一条可部署的语音意图识别链路：用户上传**越南语**音频，服务端完成音频规范化、语音识别（ASR）、中文翻译、基于大语言模型（LLM）的**中文意图分类**，并返回结构化结果。

- **主要用户**：内部系统/业务方调用方。
- **成功标准**：在典型现场短语（约 10s 内音频）上，端到端可稳定返回转写与意图；失败时可**部分返回**已成功步骤的结果，并标注各步骤状态。

---

## 2. 范围（In Scope）

| 能力 | 说明 |
|------|------|
| 音频规范化 | 每次请求**强制**用 `ffmpeg` 转为 **mono + 16kHz + PCM S16LE WAV** 后再做 ASR。 |
| ASR | 越南语转写，输出 `transcription_vi`。 |
| 翻译 | 越南语 → 中文，输出 `translation_zh`（用于对齐中文标签语义与展示）。 |
| 意图分类 | 在**有** `translation_zh` 时，将 `transcription_vi` 与 `translation_zh`**同时**输入 LLM；**翻译失败**时，**仍**仅凭 `transcription_vi` 分类（提示词须支持仅用越南语映射到中文标签）。输出固定中文类别 + 简要 `reason`。 |
| 同步 API | 单次请求同步返回（适用短音频、低并发场景）。 |

## 3. 非范围（Out of Scope）

- 暂不实现 `need_review` 等业务人工审核字段（可在后续版本增加）。
- 安全鉴权、密钥管理、限流策略：**本版 PRD 仅预留原则**（见第 8 节），实现细节由开发阶段补充。

---

## 4. 意图标签体系（固定枚举）

分类结果 `intent_category` **必须**为下列之一（字符串完全一致）：

- `生产`（人员短缺/计划变更/作业指导缺失）
- `品管`（不良品超标/物料质量疑异）
- `设备`（设备有问题）
- `工艺`（技术文件错误）
- `物料`（缺料/断料/包装破损/退补料流程卡顿）
- `IT`（网络中断/数据错误/软件Bug）
- `其他`（不属于以上类型）

> **说明**：下文若写「须为第 4 节枚举之一」，即指**本节**所列标签，不得自造类别或使用别名。

---

## 5. API 契约（逻辑层）

本节描述**逻辑契约**；具体 HTTP 路径、框架（FastAPI 等）由实现决定。

### 5.1 请求

- **内容**：仅接受**音频文件**（multipart 或等价上传方式）。
- **典型约束**：时长约 **≤ 10s**；单文件约 **500KB 量级**（非硬上限，但异常大文件可在实现中设上限）。
- **客户端格式**：允许常见容器/编码（如 `wav` / `m4a` / `mp3` 等），服务端**一律 normalize**，不依赖后缀猜测可靠性。

### 5.2 处理流程（固定顺序）

1. **Normalize**：`ffmpeg` → `mono_16k_pcm_wav`（可缓存：输入未变则复用同一路径产物，实现可选）。
2. **ASR**：对规范化 WAV 调用 ASR → `transcription_vi`。
3. **Translate**：对越南语文本调用 LLM/Qwen API → `translation_zh`（失败则 `translation_zh` 为 `null`，见 5.4）。
4. **Classify**：  
   - 若 `translation_zh` 非空：将 `transcription_vi` 与 `translation_zh` **同时**作为 LLM 输入；  
   - 若 `translation_zh` 为空（翻译失败）：**仅**将 `transcription_vi` 作为 LLM 输入；  
   - LLM 输出 `intent_category`（须为**第 4 节**枚举之一）与简洁 `reason`。

### 5.3 响应体（JSON 字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `request_id` | string | 链路追踪 ID（可取 ASR/LLM 返回 ID 或服务端生成 UUID，须贯通日志）。 |
| `transcription_vi` | string \| null | ASR 成功则有值。 |
| `translation_zh` | string \| null | 翻译成功则有值。 |
| `intent_category` | string \| null | 分类成功则须为**第 4 节「意图标签体系」**所列标签之一。 |
| `reason` | string \| null | 分类成功则有值：LLM 给出**简洁**判断依据（建议长度上限如 ≤200 字，避免冗长）。 |
| `stages` | object | 子对象见下；每一步 `status` 为 `success` / `failed`，`error` 为结构化或可读错误（失败时填写）。 |
| `timings_ms` | object \| null | 可选：normalize / asr / translate / classify 各段耗时。 |
| `raw` | object \| null | **可选**；仅用于排障（如 debug 开关开启时返回 LLM/ASR 原始片段）。默认**不返回**或置 `null`。 |

**`stages` 建议结构：**

```json
{
  "normalize": { "status": "success|failed", "error": null },
  "asr": { "status": "success|failed", "error": null },
  "translate": { "status": "success|failed", "error": null },
  "classify": { "status": "success|failed", "error": null }
}
```

### 5.4 部分返回策略

- **原则**：有多少成功步骤，就返回多少有效字段；失败步骤在对应 `stages.*` 标记 `failed` 与原因。
- **翻译失败与分类（已定稿）**：当 `translate` 为 `failed` 或 `translation_zh` 为 `null` 时，**仍执行** `classify`，**仅**使用 `transcription_vi`。提示词须明确要求：在无中文译文时，依据越南语文本推断，并输出**第 4 节**中文标签之一及 `reason`。

### 5.5 LLM 分类输出格式（给 AI/开发的硬约束）

分类调用须要求模型**只输出合法 JSON**（无 Markdown 围栏），例如：

```json
{
  "intent_category": "设备",
  "reason": "语音提到设备异常，需现场处理，故归为设备类。"
}
```

- `intent_category` 必须属于**第 4 节**枚举。
- `reason` 为非空简洁中文（或中英混合若业务需要，默认中文），说明归类依据。
- 若 JSON 无法解析、`intent_category` 不在枚举、或 `reason` 缺失/为空，则 `classify` 标 `failed`，并保留已成功前置结果。

---

## 6. 依赖与环境

| 依赖 | 说明 |
|------|------|
| `ffmpeg` | 服务端必须可用；Windows 开发可配置 `FFMPEG_EXE`，Linux 部署需安装 `ffmpeg` 或镜像内置。 |
| DashScope / Qwen | ASR 与 LLM 调用的账号与模型名由配置注入，**禁止**将 API Key 写入仓库。 |

---

## 7. 可观测性

- 每次请求记录：`request_id`、各 `stages` 结果、`timings_ms`（若有）、最终 `intent_category` / `reason`（若分类成功）。
- 日志中不对 API Key、完整原始 `raw`（若含敏感内容）做明文持久化——除非明确开启受限 debug。

---

## 8. 安全与配置（原则）

- API Key、模型名、超时、上传大小上限：**配置与密钥管理**，不进入版本库。
- 本版对外暴露接口的认证方式：**待定**（可后续单开「安全设计」小节）。

---

## 9. 验收标准（V1）

1. 给定一批 **≤10s** 的规范化前音频样本，normalize → ASR → 翻译 → 分类链路可**稳定跑通**（无 indefinite hang；网络/API 错误有明确 `stages` 失败信息）。
2. 分类成功时：`intent_category` 必为**第 4 节**枚举之一；`reason` 非空且简洁可读。
3. 翻译失败时：仍可按 5.4 仅凭 `transcription_vi` 完成分类，或若 ASR 也失败则 `classify` 合理失败；任一步失败时响应满足部分返回约定，且不因单步失败导致进程卡死。

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1 | 2026-03-26 | 初稿：同步 API、强制 normalize、ASR+翻译+分类、可选 raw。 |
| 0.2 | 2026-03-26 | 移除 confidence；分类输出改为 `intent_category` + `reason`；第 4 节引用说明；5.4 定稿「翻译失败仍仅用越南语分类」。 |
