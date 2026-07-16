import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.APP_NAME = os.getenv("APP_NAME", "Converigo")
        self.APP_VERSION = os.getenv("APP_VERSION", "3.0.0")
        self.UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
        self.OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
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
        self.GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")
        self.RATE_LIMIT_CONVERT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_CONVERT_REQUESTS_PER_MINUTE", "30"))
        self.RATE_LIMIT_UPLOAD_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_UPLOAD_REQUESTS_PER_MINUTE", "20"))
        self.RATE_LIMIT_API_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_API_REQUESTS_PER_MINUTE", "60"))
        self.RATE_LIMIT_OTHER_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_OTHER_REQUESTS_PER_MINUTE", "120"))

        default_allowed_hosts = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "testserver",
            "100.64.0.2",
            "100.64.0.2:8080",
            "converigo.com",
            "www.converigo.com",
            "*.railway.app",
            "*.up.railway.app",
            "*.railway.internal",
        ]
        allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "").strip()
        if allowed_hosts_env:
            self.ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]
        else:
            self.ALLOWED_HOSTS = default_allowed_hosts


settings = Settings()
