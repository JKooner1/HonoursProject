from pydantic import BaseModel
from pathlib import Path

class Settings(BaseModel):
    project_name: str = "Retail Analytics"
    data_dir: Path = Path("data")
    db_path: Path = Path("data/retail.db")

settings = Settings()
