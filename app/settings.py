from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    project_name: str = "Retail Analytics"
    data_dir: Path = Path("data")
    parquet_path: Path = Path("data/sales.parquet")


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)