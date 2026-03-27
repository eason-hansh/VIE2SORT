import pytest
from fastapi.testclient import TestClient

pytest.importorskip("multipart")

from vietsort_service.api import main as api_main
from vietsort_service.config import Settings
from vietsort_service.models import IntentResponse, StageMap, StageStatus

app = api_main.app


def test_healthz():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def _fake_settings() -> Settings:
    return Settings(
        dashscope_api_key="test-key",
        asr_model="gummy-realtime-v1",
        llm_model="qwen3-max",
        ffmpeg_exe="ffmpeg",
        max_upload_size_mb=5,
        request_timeout_seconds=30,
        persist_normalized_audio=False,
        normalized_audio_dir="tmp/normalized",
    )


def test_intent_all_success_returns_200(monkeypatch):
    def fake_run_pipeline(_path, _settings):
        return IntentResponse(
            request_id="req-1",
            transcription_vi="Máy 1 thiết bị bất thường.",
            translation_zh="1号机设备异常。",
            intent_category="设备",
            reason="明确指向设备异常。",
            stages=StageMap(
                normalize=StageStatus(status="success"),
                asr=StageStatus(status="success"),
                translate=StageStatus(status="success"),
                classify=StageStatus(status="success"),
            ),
        )

    monkeypatch.setattr(api_main, "load_settings", _fake_settings)
    monkeypatch.setattr(api_main, "run_pipeline", fake_run_pipeline)

    client = TestClient(app)
    resp = client.post("/v1/intent", files={"audio": ("a.wav", b"123", "audio/wav")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent_category"] == "设备"
    assert body["reason"]


def test_intent_partial_success_returns_207(monkeypatch):
    def fake_run_pipeline(_path, _settings):
        return IntentResponse(
            request_id="req-2",
            transcription_vi="Máy 1 thiết bị bất thường.",
            translation_zh=None,
            intent_category="设备",
            reason="仅凭越南语也可判断设备异常。",
            stages=StageMap(
                normalize=StageStatus(status="success"),
                asr=StageStatus(status="success"),
                translate=StageStatus(status="failed", error="timeout"),
                classify=StageStatus(status="success"),
            ),
        )

    monkeypatch.setattr(api_main, "load_settings", _fake_settings)
    monkeypatch.setattr(api_main, "run_pipeline", fake_run_pipeline)

    client = TestClient(app)
    resp = client.post("/v1/intent", files={"audio": ("a.wav", b"123", "audio/wav")})
    assert resp.status_code == 207
    body = resp.json()
    assert body["stages"]["translate"]["status"] == "failed"
