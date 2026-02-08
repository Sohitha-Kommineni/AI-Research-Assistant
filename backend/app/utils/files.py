import os
from pathlib import Path
from typing import BinaryIO


BASE_STORAGE = Path(os.getenv("STORAGE_DIR", "storage"))


def ensure_storage() -> Path:
    BASE_STORAGE.mkdir(parents=True, exist_ok=True)
    return BASE_STORAGE


def save_upload(file_obj: BinaryIO, filename: str) -> Path:
    ensure_storage()
    safe_name = filename.replace(" ", "_")
    path = BASE_STORAGE / safe_name
    with path.open("wb") as f:
        f.write(file_obj.read())
    return path
