from fastapi import FastAPI
from services.scanner.config import ScannerConfig
from services.scanner.api import router as policy_router, scans_router

config = ScannerConfig()

app = FastAPI(
    title="Local Scanner Service",
    description="Local-only FastAPI scanner service shell",
    version=config.version
)

app.include_router(policy_router)
app.include_router(scans_router)

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
