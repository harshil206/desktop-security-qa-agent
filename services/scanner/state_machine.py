from typing import Set, Dict
from packages.contracts.schemas import ScanStatus

class InvalidStateTransitionError(ValueError):
    """Raised when an invalid scan status transition is attempted."""
    pass

# Transition Graph: Defines permitted target states for each current status
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    ScanStatus.DRAFT.value: {ScanStatus.SCOPE_VALIDATED.value, ScanStatus.CANCELLED.value},
    ScanStatus.SCOPE_VALIDATED.value: {ScanStatus.QUEUED.value, ScanStatus.CANCELLED.value},
    ScanStatus.QUEUED.value: {ScanStatus.RUNNING.value, ScanStatus.CANCELLED.value},
    ScanStatus.RUNNING.value: {
        ScanStatus.COMPLETED.value,
        ScanStatus.FAILED.value,
        ScanStatus.CANCELLED.value,
        ScanStatus.BLOCKED.value,
    },
    ScanStatus.COMPLETED.value: set(),
    ScanStatus.FAILED.value: set(),
    ScanStatus.CANCELLED.value: set(),
    ScanStatus.BLOCKED.value: set(),
}

def validate_state_transition(current_state: str, new_state: str) -> None:
    if current_state not in VALID_TRANSITIONS:
        raise InvalidStateTransitionError(f"Unknown current status '{current_state}'.")
    
    allowed = VALID_TRANSITIONS[current_state]
    if new_state not in allowed:
        raise InvalidStateTransitionError(
            f"Invalid status transition from '{current_state}' to '{new_state}'. "
            f"Allowed target states: {sorted(list(allowed)) or 'None (Terminal state)'}"
        )
