from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ImportStatus(Enum):
    QUARANTINED = "QUARANTINED"
    SCAN_PENDING = "SCAN_PENDING"
    NEXUS_BOUND = "NEXUS_BOUND"
    RELEASE_REQUESTED = "RELEASE_REQUESTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SANITIZED_RESTORE_READY = "SANITIZED_RESTORE_READY"
    EXPORT_DENIED = "EXPORT_DENIED"
    DELETED = "DELETED"


@dataclass
class ImportedAIRecord:
    import_id: str
    original_name: str
    imported_at: datetime = field(default_factory=datetime.utcnow)
    source_type: str = "unknown"
    original_snapshot_path: str = ""
    working_copy_ai_uuid: str = ""
    status: ImportStatus = ImportStatus.QUARANTINED
    accepted_disclaimer: bool = False
    review_notes: str = ""
    checksum_original: str = ""
    checksum_working_copy: str = ""
