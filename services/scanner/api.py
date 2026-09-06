from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ValidationError
from packages.contracts.schemas import ScanPolicy
from services.scanner.db import init_db, create_scan_record, get_scan_record, update_scan_status, get_scan_history
from services.scanner.state_machine import InvalidStateTransitionError

router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])
scans_router = APIRouter(prefix="/api/v1/scans", tags=["Scans"])

# Global in-memory DB connection for local scanner service shell
db_conn = init_db(":memory:")

@router.post("/validate")
def validate_policy(policy_data: dict):
    """
    Validate a scan policy payload against authorization, scope, budget, and passive mode rules.
    Does NOT initiate any network target calls.
    """
    try:
        policy = ScanPolicy(**policy_data)
        return {
            "valid": True,
            "policy": policy
        }
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return {
            "valid": False,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scan policy payload: {str(e)}"
        )

@router.post("")
def create_policy(policy: ScanPolicy):
    """
    Create and validate a scan policy instance.
    """
    return {
        "status": "validated",
        "policy": policy
    }


class CreateScanRequest(BaseModel):
    scan_id: str
    policy: ScanPolicy

class UpdateStatusRequest(BaseModel):
    status: str
    reason: Optional[str] = None


@scans_router.post("", status_code=status.HTTP_201_CREATED)
def create_scan(req: CreateScanRequest):
    """Create a durable scan record in draft state."""
    scan = create_scan_record(
        db_conn,
        scan_id=req.scan_id,
        target_domains=req.policy.target_domains,
        policy_dict=req.policy.model_dump(mode="json")
    )
    return scan


@scans_router.get("/{scan_id}")
def get_scan(scan_id: str):
    """Get scan record and transition history."""
    scan = get_scan_record(db_conn, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found.")
    history = get_scan_history(db_conn, scan_id)
    return {
        "scan": scan,
        "history": history
    }


@scans_router.patch("/{scan_id}/status")
def patch_scan_status(scan_id: str, req: UpdateStatusRequest):
    """Transition scan job status with reason code validation."""
    try:
        scan = update_scan_status(db_conn, scan_id, req.status, req.reason)
        return scan
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
