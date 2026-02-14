"""Configuração central da aplicação."""

from pathlib import Path

from pydantic_settings import BaseSettings


_PROJECT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class Settings(BaseSettings):
    app_name: str = "Y"
    data_dir: Path = _PROJECT_DATA_DIR
    database_url: str = f"sqlite+aiosqlite:///{(_PROJECT_DATA_DIR / 'y_project.db').as_posix()}"
    cvm_base_url: str = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS"
    b3_cotahist_url: str = (
        "https://bvmf.bmfbovespa.com.br/InstDados/SerHist"
    )
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    debug: bool = True

    class Config:
        env_prefix = "Y_"


settings = Settings()
