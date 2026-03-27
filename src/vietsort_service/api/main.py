import asyncio
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from vietsort_service.config import load_settings
from vietsort_service.logging_utils import setup_json_logging
from vietsort_service.pipeline import run_pipeline

setup_json_logging()
app = FastAPI(title="Vie2Sort Intent API", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v1/intent")
async def intent(audio: UploadFile = File(...)):
    """
    单文件音频识别入口：
    1) 接收 multipart 的 audio 文件
    2) 做基础校验（空文件、大小限制）
    3) 调用 pipeline（normalize -> asr -> translate -> classify）
    4) 按 stages 是否全部成功返回 200 或 207
    """
    settings = load_settings()
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="audio 文件为空")
    if len(data) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"音频超过 {settings.max_upload_size_mb}MB 限制")

    # 写入临时文件，便于后续统一走文件路径处理链路
    suffix = Path(audio.filename or "upload.bin").suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        try:
            # run_pipeline 是同步阻塞流程（normalize/asr/llm），通过 run_in_threadpool 放到线程池执行以避免阻塞事件循环；
            # 外层 asyncio.wait_for 增加总超时控制。
            result = await asyncio.wait_for(
                run_in_threadpool(run_pipeline, tmp_path, settings),
                timeout=settings.request_timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="请求处理超时")
    finally:
        # 原始上传文件始终删除，避免磁盘堆积
        if tmp_path.exists():
            tmp_path.unlink()

    all_success = all(
        [
            result.stages.normalize.status == "success",
            result.stages.asr.status == "success",
            result.stages.translate.status == "success",
            result.stages.classify.status == "success",
        ]
    )
    # 约定：全成功 200，部分成功 207
    status_code = 200 if all_success else 207
    return JSONResponse(status_code=status_code, content=result.model_dump())
