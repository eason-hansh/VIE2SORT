from pathlib import Path

from vietsort_service.config import load_settings
from vietsort_service.pipeline import run_pipeline


def main():
    settings = load_settings()
    input_path = Path(r"raw_data/new/注塑1号机设备异常.m4a")
    result = run_pipeline(input_path, settings)
    print(result.model_dump())


if __name__ == "__main__":
    main()
