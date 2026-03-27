def transcribe_vi(audio_wav_path: str, api_key: str, model: str) -> tuple[str, str | None]:
    """
    调用 DashScope ASR，返回：
    - transcription 文本（拼接后的最终文本）
    - request_id（用于链路追踪）
    """
    import dashscope
    from dashscope.audio.asr import TranslationRecognizerRealtime

    dashscope.api_key = api_key
    recognizer = TranslationRecognizerRealtime(
        model=model,
        format="wav",
        sample_rate=16000,
        source_language="vi",
        transcription_enabled=True,
        translation_enabled=False,
        callback=None,
    )
    result = recognizer.call(audio_wav_path)
    if getattr(result, "error_message", None):
        raise RuntimeError(str(result.error_message))

    # 非流式返回可能含多段结果，这里统一拼接成单文本
    parts: list[str] = []
    for item in getattr(result, "transcription_result_list", []) or []:
        if item and getattr(item, "text", None):
            parts.append(item.text)

    request_id = getattr(result, "request_id", None)
    return "\n".join(parts).strip(), request_id
