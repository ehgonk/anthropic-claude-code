from pathlib import Path
from pydantic_settings import BaseSettings

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_DATA_DIR = PROJECT_ROOT / "data"
PROJECT_DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    app_name: str = "Broker - Bolsa de Valores API"
    data_dir: Path = PROJECT_DATA_DIR
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_DATA_DIR}/broker.db"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    # Data Sources
    brapi_base_url: str = "https://brapi.dev/api"

    class Config:
        env_prefix = "BROKER_"


settings = Settings()
