import pytest

from vietsort_service.services.llm import _extract_json_block


def test_extract_json_block_plain():
    data = _extract_json_block('{"intent_category":"设备","reason":"设备异常"}')
    assert data["intent_category"] == "设备"
    assert data["reason"] == "设备异常"


def test_extract_json_block_markdown():
    text = """```json
{"intent_category":"IT","reason":"网络中断"}
```"""
    data = _extract_json_block(text)
    assert data["intent_category"] == "IT"


def test_extract_json_block_invalid():
    with pytest.raises(Exception):
        _extract_json_block("not json")
