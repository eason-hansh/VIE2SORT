import json
import re

from vietsort_service.models import INTENT_LABELS


def _extract_json_block(text: str) -> dict:
    """
    从 LLM 文本中提取 JSON：
    - 支持纯 JSON
    - 支持 ```json ... ``` 包裹
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    return json.loads(text)


def translate_and_classify(
    transcription_vi: str,
    api_key: str,
    model: str,
) -> tuple[str, str, str, dict]:
    """
    单次 LLM 调用同时完成：
    - 越南语 -> 中文翻译
    - 意图分类（固定枚举）
    - 分类原因输出
    """
    import dashscope
    from dashscope import Generation

    dashscope.api_key = api_key

    label_text = "、".join(INTENT_LABELS)
    prompt = (
        "你是工厂问题分析助手。请先将越南语转写准确翻译成中文，再进行意图分类。"
        f"分类时请从以下固定类别中选择唯一一个：{label_text}。\n"
        "输出必须是 JSON，且仅包含以下字段：translation_zh、intent_category、reason。\n"
        "reason 要简洁（不超过80字）。\n"
    )
    user_content = f"越南语转写：{transcription_vi}\n"
    user_content += (
        "请仅输出 JSON，例如："
        '{"translation_zh":"1号机原料异常","intent_category":"物料","reason":"提到原料异常，归为物料"}'
    )

    response = Generation.call(
        api_key=api_key,
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
        result_format="message",
        enable_thinking=False,
    )
    if response.status_code != 200:
        raise RuntimeError(f"{response.code}: {response.message}")
    content = response.output.choices[0].message.content
    parsed = _extract_json_block(content)
    translation_zh = str(parsed.get("translation_zh", "")).strip()
    intent = str(parsed.get("intent_category", "")).strip()
    reason = str(parsed.get("reason", "")).strip()
    if not translation_zh:
        raise RuntimeError("translation_zh 为空")
    if intent not in INTENT_LABELS:
        raise RuntimeError(f"intent_category 不在枚举内: {intent}")
    if not reason:
        raise RuntimeError("reason 为空")
    return translation_zh, intent, reason, {"model": model, "content": content}


def translate_vi_to_zh(text_vi: str, api_key: str, model: str) -> tuple[str, dict]:
    """兼容旧实验脚本：仅返回翻译结果。"""
    translation_zh, _, _, raw = translate_and_classify(
        transcription_vi=text_vi,
        api_key=api_key,
        model=model,
    )
    return translation_zh, raw
