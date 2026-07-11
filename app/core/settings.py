import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.APP_NAME = os.getenv("APP_NAME", "Convertin")
        self.APP_VERSION = os.getenv("APP_VERSION", "3.0.0")
        self.UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
        self.OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
        self.LOG_DIR = Path(os.getenv("LOG_DIR", "app/logs"))
        self.LOG_FILE = self.LOG_DIR / os.getenv("LOG_FILE", "app.log")
        self.MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
        self.MAX_UPLOAD_SIZE = self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.FILE_RETENTION_SECONDS = int(os.getenv("FILE_RETENTION_SECONDS", "3600"))
        self.MAX_FILENAME_LENGTH = int(os.getenv("MAX_FILENAME_LENGTH", "255"))


settings = Settings()
