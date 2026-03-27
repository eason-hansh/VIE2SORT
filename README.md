# Vie2Sort Intent Service

越南语音频意图识别服务（FastAPI）。

## 环境要求

- Python 3.10（建议 conda 环境）
- ffmpeg（Linux 用 PATH，Windows 可配置 `FFMPEG_EXE`）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 必要环境变量

- `DASHSCOPE_API_KEY`：DashScope API Key（必填）
- `FFMPEG_EXE`：可选，Windows 下建议配置为 `ffmpeg.exe` 绝对路径
- `ASR_MODEL`：可选，默认 `gummy-realtime-v1`
- `LLM_MODEL`：可选，默认 `qwen-flash`
- `REQUEST_TIMEOUT_SECONDS`：可选，默认 `30`
- `MAX_UPLOAD_SIZE_MB`：可选，默认 `5`
- `PERSIST_NORMALIZED_AUDIO`：可选，默认 `false`
- `NORMALIZED_AUDIO_DIR`：可选，默认 `tmp/normalized`

## 启动服务

```bash
uvicorn vietsort_service.api.main:app --host 0.0.0.0 --port 8000
```

> 如果你在项目根目录启动，建议设置 `PYTHONPATH=src`（Windows PowerShell：`$env:PYTHONPATH='src'`）。

## 接口

- `POST /v1/intent`
- `multipart/form-data`，文件字段名：`audio`

返回规则：
- 全部成功：HTTP `200`
- 部分成功：HTTP `207`

### cURL 调用示例

```bash
curl -X POST "http://127.0.0.1:8000/v1/intent" \
  -H "accept: application/json" \
  -F "audio=@raw_data/new/注塑1号机设备异常.m4a"
```

### 响应示例（200）

```json
{
  "request_id": "8f4f6b6d4a9a4f47a8897ccad52b1f2e",
  "transcription_vi": "Máy 1 thiết bị bất thường.",
  "translation_zh": "1号机设备异常。",
  "intent_category": "设备",
  "reason": "描述明确指向设备异常，归类为设备问题。",
  "stages": {
    "normalize": {"status": "success", "error": null},
    "asr": {"status": "success", "error": null},
    "translate": {"status": "success", "error": null},
    "classify": {"status": "success", "error": null}
  },
  "timings_ms": {"normalize": 38, "asr": 1260, "translate_classify": 1350},
  "raw": null
}
```

### 响应示例（207，部分成功）

```json
{
  "request_id": "f0e0f5211cf24d249d4f5f8c8c5f002a",
  "transcription_vi": "Máy 1 thiết bị bất thường.",
  "translation_zh": null,
  "intent_category": "设备",
  "reason": "越南语转写提到设备异常。",
  "stages": {
    "normalize": {"status": "success", "error": null},
    "asr": {"status": "success", "error": null},
    "translate": {"status": "failed", "error": "translate timeout"},
    "classify": {"status": "success", "error": null}
  },
  "timings_ms": {"normalize": 41, "asr": 1190, "translate_classify": 680},
  "raw": null
}
```

## 实验脚本归档

- 历史实验脚本已归档到 `scripts/legacy/`
- 当前建议使用：
  - `scripts/experiment_asr.py`
  - `scripts/experiment_translate.py`
  - `scripts/normalize_audio_test.py`

## 运行测试

```bash
pytest -q
```
