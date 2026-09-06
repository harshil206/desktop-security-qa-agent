from fastapi import FastAPI
from services.scanner.config import ScannerConfig

config = ScannerConfig()

app = FastAPI(
    title="Local Scanner Service",
    description="Local-only FastAPI scanner service shell",
    version=config.version
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "scanner"
    }

@app.get("/version")
def get_version():
    return {
        "version": config.version
    }
