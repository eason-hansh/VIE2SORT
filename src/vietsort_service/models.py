from typing import Literal

from pydantic import BaseModel, Field


INTENT_LABELS = ["生产", "品管", "设备", "工艺", "物料", "IT", "其他"]


# 该类用于描述 单个阶段（如：asr, translation等） 的状态
# 继承 pydantic.BaseModel。BaseModel 会自动初始化
class StageStatus(BaseModel):
    status: Literal["success", "failed"]  # literal,枚举的简便写法
    error: str | None = None  # str 或 空，'= None' --> 默认空


# 该类用于把所有阶段（normalize/asr/translate/classify）的 StageStatus 组合在一起
# Field “字段配置器”，用来给字段设置默认值、校验规则、描述等
# 通过 default_factory 每次新建一个 StageStatus(status="failed")
# 用 default_factory，避免不同实例共享同一个默认对象。
class StageMap(BaseModel):
    normalize: StageStatus = Field(default_factory=lambda: StageStatus(status="failed"))
    asr: StageStatus = Field(default_factory=lambda: StageStatus(status="failed"))
    translate: StageStatus = Field(default_factory=lambda: StageStatus(status="failed"))
    classify: StageStatus = Field(default_factory=lambda: StageStatus(status="failed"))


# 该类用于记录返回结果
class IntentResponse(BaseModel):
    request_id: str
    transcription_vi: str | None = None
    translation_zh: str | None = None
    intent_category: str | None = None
    reason: str | None = None
    stages: StageMap
    timings_ms: dict[str, int] | None = None
    raw: dict | None = None
