from vietsort_service.config import load_settings
from vietsort_service.services.llm import translate_vi_to_zh


def main():
    settings = load_settings()
    text_vi = "Máy 1 thiết bị bất thường. Máy 1 thiết bị."
    zh, raw = translate_vi_to_zh(
        text_vi=text_vi,
        api_key=settings.dashscope_api_key,
        model=settings.llm_model,
    )
    print("translation_zh:", zh)
    print("raw:", raw)


if __name__ == "__main__":
    main()
