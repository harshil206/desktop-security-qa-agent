from pydantic import BaseModel, Field, field_validator

ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

class ScannerConfig(BaseModel):
    host: str = Field(default="127.0.0.1", description="Host address for the local scanner service.")
    port: int = Field(default=8000, ge=1024, le=65535, description="Port for the local scanner service.")
    version: str = Field(default="0.1.0", description="Service version.")

    @field_validator("host")
    @classmethod
    def validate_loopback_host(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ALLOWED_LOOPBACK_HOSTS:
            raise ValueError(
                f"Invalid host '{v}'. Scanner service must bind strictly to loopback host "
                f"('127.0.0.1', 'localhost', or '::1'). External or LAN interface bindings are rejected."
            )
        return cleaned
