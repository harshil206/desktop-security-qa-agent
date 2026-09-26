import os
from datetime import datetime
from typing import Dict, Any, Optional, Union, Tuple
from packages.contracts.schemas import EvidenceRef, ArtifactType
from services.scanner.storage.redactor import (
    redact_text_content,
    redact_url_query_params,
    redact_evidence_metadata
)

DEFAULT_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "outputs", "scans"))


class ArtifactStore:
    """
    Disk-backed storage manager for scan evidence artifacts.

    Responsibilities:
    1. Persists raw artifact data (screenshots, DOM snapshots, network traces, logs) in isolated scan directories.
    2. Redacts sensitive credentials, tokens, cookies, and parameters before generating EvidenceRef objects.
    3. Provides retrieval helper for user display and reporting interfaces.
    """

    def __init__(self, base_output_dir: Optional[str] = None):
        self.base_output_dir = os.path.abspath(base_output_dir or DEFAULT_OUTPUT_DIR)

    def get_scan_artifact_dir(self, scan_id: str) -> str:
        """Get scan artifacts directory path and create if missing."""
        scan_dir = os.path.join(self.base_output_dir, scan_id, "artifacts")
        os.makedirs(scan_dir, exist_ok=True)
        return scan_dir

    def save_artifact(
        self,
        scan_id: str,
        artifact_id: str,
        artifact_type: ArtifactType,
        content: Union[str, bytes],
        location_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceRef:
        """
        Save artifact content to disk and return a redacted EvidenceRef object.
        """
        artifact_dir = self.get_scan_artifact_dir(scan_id)

        # File extension based on artifact type
        ext = ".png" if artifact_type == ArtifactType.SCREENSHOT else ".txt"
        file_path = os.path.join(artifact_dir, f"{artifact_id}{ext}")

        # Write raw content to disk
        if isinstance(content, bytes):
            with open(file_path, "wb") as f:
                f.write(content)
            content_size = len(content)
            snippet = f"Binary artifact ({content_size} bytes)"
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            content_size = len(content.encode("utf-8"))
            redacted_content = redact_text_content(content)
            snippet = redacted_content[:200].strip().replace("\n", " ")
            if len(redacted_content) > 200:
                snippet += "..."

        # Sanitize metadata & URL
        clean_url = redact_url_query_params(location_url)
        clean_metadata = redact_evidence_metadata(metadata or {})
        clean_metadata["stored_filepath"] = file_path
        clean_metadata["size_bytes"] = content_size

        return EvidenceRef(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            location_url=clean_url,
            timestamp=datetime.now(),
            snippet_or_description=snippet or f"Stored {artifact_type.value} artifact ({artifact_id})",
            metadata=clean_metadata
        )

    def get_artifact_filepath(self, scan_id: str, artifact_id: str) -> Optional[str]:
        """Find filepath of stored artifact by ID."""
        artifact_dir = self.get_scan_artifact_dir(scan_id)
        for ext in (".png", ".txt", ".json"):
            file_path = os.path.join(artifact_dir, f"{artifact_id}{ext}")
            if os.path.exists(file_path):
                return file_path
        return None

    def read_artifact(self, scan_id: str, artifact_id: str) -> Tuple[Union[str, bytes], str]:
        """Read artifact content and return (content, mime_type)."""
        filepath = self.get_artifact_filepath(scan_id, artifact_id)
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"Artifact '{artifact_id}' not found for scan '{scan_id}'.")

        if filepath.endswith(".png"):
            with open(filepath, "rb") as f:
                return f.read(), "image/png"
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read(), "text/plain"
