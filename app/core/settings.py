import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "true" if self.ENVIRONMENT == "development" else "false").lower() in {"1", "true", "yes", "on"}
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "debug" if self.DEBUG else "info")
        self.ALLOWED_HOSTS = [
            host.strip()
            for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
            if host.strip()
        ]
        self.APP_NAME = os.getenv("APP_NAME", "Convertin")
        self.APP_VERSION = os.getenv("APP_VERSION", "3.0.0")
        self.UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).expanduser()
        self.OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs")).expanduser()
        self.LOG_DIR = Path(os.getenv("LOG_DIR", "app/logs"))
        self.LOG_FILE = self.LOG_DIR / os.getenv("LOG_FILE", "app.log")
        self.MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
        self.MAX_UPLOAD_SIZE = self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.FILE_RETENTION_SECONDS = int(os.getenv("FILE_RETENTION_SECONDS", "3600"))
        self.OUTPUT_RETENTION_MINUTES = int(os.getenv("OUTPUT_RETENTION_MINUTES", "60"))
        self.OUTPUT_RETENTION_SECONDS = self.OUTPUT_RETENTION_MINUTES * 60
        self.CONVERSION_TIMEOUT_SECONDS = int(os.getenv("CONVERSION_TIMEOUT_SECONDS", "300"))
        self.VIDEO_CONVERSION_TIMEOUT_SECONDS = int(os.getenv("VIDEO_CONVERSION_TIMEOUT_SECONDS", str(self.CONVERSION_TIMEOUT_SECONDS)))
        self.AUDIO_CONVERSION_TIMEOUT_SECONDS = int(os.getenv("AUDIO_CONVERSION_TIMEOUT_SECONDS", str(self.CONVERSION_TIMEOUT_SECONDS)))
        self.IMAGE_CONVERSION_TIMEOUT_SECONDS = int(os.getenv("IMAGE_CONVERSION_TIMEOUT_SECONDS", str(self.CONVERSION_TIMEOUT_SECONDS)))
        self.DOCUMENT_CONVERSION_TIMEOUT_SECONDS = int(os.getenv("DOCUMENT_CONVERSION_TIMEOUT_SECONDS", str(self.CONVERSION_TIMEOUT_SECONDS)))
        self.MAX_FILENAME_LENGTH = int(os.getenv("MAX_FILENAME_LENGTH", "255"))


settings = Settings()
