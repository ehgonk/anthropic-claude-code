"""Configuração central da aplicação."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Radar Insider"
    database_url: str = "sqlite+aiosqlite:///./data/radar_insider.db"
    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data"
    cvm_base_url: str = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS"
    b3_cotahist_url: str = (
        "https://bvmf.bmfbovespa.com.br/InstDados/SerHist"
    )
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    debug: bool = True

    class Config:
        env_prefix = "RADAR_"


settings = Settings()
