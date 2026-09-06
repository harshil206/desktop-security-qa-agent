from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from packages.contracts.schemas import ScanPolicy

router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])

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
