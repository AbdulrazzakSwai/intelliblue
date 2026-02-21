from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import os


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://intelliblue:intelliblue@localhost:5432/intelliblue",
        alias="DATABASE_URL"
    )

    # JWT
    secret_key: str = Field(default="change-me-in-production-use-long-random-string", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Storage
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    # LLM
    llm_model_path: str = Field(default="./models/model.gguf", alias="LLM_MODEL_PATH")
    llm_n_gpu_layers: int = Field(default=0, alias="LLM_N_GPU_LAYERS")
    llm_n_ctx: int = Field(default=4096, alias="LLM_N_CTX")
    llm_max_tokens: int = Field(default=1024, alias="LLM_MAX_TOKENS")

    # Correlation config
    correlation_config_path: str = Field(
        default="./config/correlation_config.json",
        alias="CORRELATION_CONFIG_PATH"
    )
    siem_mapping_path: str = Field(
        default="./config/siem_mapping.json",
        alias="SIEM_MAPPING_PATH"
    )

    # App
    app_name: str = "IntelliBlue SOC"
    debug: bool = Field(default=False, alias="DEBUG")

    model_config = {"populate_by_name": True, "env_file": ".env"}


settings = Settings()
