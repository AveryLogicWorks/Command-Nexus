"""
Moirai Ledger - Local Field Code Registry
===========================================
Local-first field code system for Command Nexus.
Manages Hermes Codes (field codes) for in-person distribution.

Customer-facing names:
- Field codes: Hermes Codes
- Activation: Prometheus Activation
- Registry: Moirai Ledger
- Storage: Hestia Vault

Code lifecycle:
INACTIVE → ACTIVE → REDEEMED → EXPIRED → VOIDED
"""

import json
import csv
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List
import uuid


class CodeStatus(Enum):
    """Field code lifecycle states."""
    INACTIVE = "INACTIVE"  # Code exists but cannot be redeemed yet
    ACTIVE = "ACTIVE"      # Chad activated it, customer can redeem
    REDEEMED = "REDEEMED"  # Customer used it once, cannot be used again
    EXPIRED = "EXPIRED"    # Time-limited access ended
    VOIDED = "VOIDED"      # Chad manually killed the code


class CodeTier(Enum):
    """Field code tiers (customer-facing only)."""
    TRIAL_7_DAY = "TRIAL_7_DAY"
    PRO = "PRO"
    BUSINESS = "BUSINESS"
    UNLIMITED = "UNLIMITED"
    ENTERPRISE_EVAL = "ENTERPRISE_EVAL"
    ENTERPRISE_PROPERTY = "ENTERPRISE_PROPERTY"
    ENTERPRISE_CORPORATE = "ENTERPRISE_CORPORATE"


class IssueType(Enum):
    """How a code was issued."""
    GENERATED = "GENERATED"  # Created in system
    ISSUED = "ISSUED"        # Given to recipient
    SOLD = "SOLD"            # Paid sale


class FieldCode:
    """Individual field code record."""

    def __init__(
        self,
        code: str,
        label: str,
        tier: CodeTier,
        status: CodeStatus = CodeStatus.INACTIVE,
        issue_type: IssueType = IssueType.GENERATED,
        issue_date: Optional[str] = None,
        activation_date: Optional[str] = None,
        redemption_date: Optional[str] = None,
        expiration_date: Optional[str] = None,
        recipient_name: Optional[str] = None,
        company: Optional[str] = None,
        contact_info: Optional[str] = None,
        payment_method: Optional[str] = None,
        payment_amount: Optional[float] = None,
        receipt_path: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        self.code = code
        self.label = label
        self.tier = tier
        self.status = status
        self.issue_type = issue_type
        self.issue_date = issue_date or datetime.utcnow().isoformat()
        self.activation_date = activation_date
        self.redemption_date = redemption_date
        self.expiration_date = expiration_date
        self.recipient_name = recipient_name
        self.company = company
        self.contact_info = contact_info
        self.payment_method = payment_method
        self.payment_amount = payment_amount
        self.receipt_path = receipt_path
        self.notes = notes
        self.customer_facing_only = True
        self.owner_aegis_excluded = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/CSV storage."""
        return {
            "code": self.code,
            "label": self.label,
            "tier": self.tier.value,
            "status": self.status.value,
            "issue_type": self.issue_type.value,
            "issue_date": self.issue_date,
            "activation_date": self.activation_date,
            "redemption_date": self.redemption_date,
            "expiration_date": self.expiration_date,
            "recipient_name": self.recipient_name,
            "company": self.company,
            "contact_info": self.contact_info,
            "payment_method": self.payment_method,
            "payment_amount": self.payment_amount,
            "receipt_path": self.receipt_path,
            "notes": self.notes,
            "customer_facing_only": self.customer_facing_only,
            "owner_aegis_excluded": self.owner_aegis_excluded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FieldCode":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            label=data["label"],
            tier=CodeTier(data["tier"]),
            status=CodeStatus(data["status"]),
            issue_type=IssueType(data["issue_type"]),
            issue_date=data["issue_date"],
            activation_date=data.get("activation_date"),
            redemption_date=data.get("redemption_date"),
            expiration_date=data.get("expiration_date"),
            recipient_name=data.get("recipient_name"),
            company=data.get("company"),
            contact_info=data.get("contact_info"),
            payment_method=data.get("payment_method"),
            payment_amount=data.get("payment_amount"),
            receipt_path=data.get("receipt_path"),
            notes=data.get("notes"),
        )


class MoiraiLedger:
    """
    Moirai Ledger - Local field code registry.
    Manages Hermes Codes for in-person distribution.
    """

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            # Default to field_keys_today in project root
            self.base_path = Path(__file__).parent.parent.parent / "field_keys_today"
        else:
            self.base_path = Path(base_path)

        self.base_path.mkdir(parents=True, exist_ok=True)

        self.ledger_json = self.base_path / "field_license_ledger.json"
        self.ledger_csv = self.base_path / "field_license_ledger.csv"
        self.ledger_txt = self.base_path / "field_license_ledger.txt"
        self.one_code_folder = self.base_path / "one_code_per_file"
        self.receipts_folder = self.base_path / "receipts"

        self.one_code_folder.mkdir(exist_ok=True)
        self.receipts_folder.mkdir(exist_ok=True)

        self._codes: Dict[str, FieldCode] = {}
        self._load_ledger()

    def _load_ledger(self):
        """Load ledger from JSON file."""
        if self.ledger_json.exists():
            try:
                with open(self.ledger_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for code_data in data.get("codes", []):
                        code = FieldCode.from_dict(code_data)
                        self._codes[code.code] = code
            except (json.JSONDecodeError, IOError):
                self._codes = {}
        else:
            self._codes = {}

    def _save_ledger(self):
        """Save ledger to JSON, CSV, and TXT files."""
        # Save JSON
        data = {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "codes": [code.to_dict() for code in self._codes.values()],
        }
        with open(self.ledger_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Save CSV
        with open(self.ledger_csv, "w", newline="", encoding="utf-8") as f:
            if self._codes:
                writer = csv.DictWriter(f, fieldnames=list(self._codes.values())[0].to_dict().keys())
                writer.writeheader()
                for code in self._codes.values():
                    writer.writerow(code.to_dict())

        # Save TXT (human-readable)
        with open(self.ledger_txt, "w", encoding="utf-8") as f:
            f.write("Moirai Ledger - Field Code Registry\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Last Updated: {datetime.utcnow().isoformat()}\n")
            f.write(f"Total Codes: {len(self._codes)}\n\n")
            for code in sorted(self._codes.values(), key=lambda c: c.code):
                f.write(f"Code: {code.code}\n")
                f.write(f"  Label: {code.label}\n")
                f.write(f"  Tier: {code.tier.value}\n")
                f.write(f"  Status: {code.status.value}\n")
                f.write(f"  Issue Type: {code.issue_type.value}\n")
                f.write(f"  Issue Date: {code.issue_date}\n")
                if code.activation_date:
                    f.write(f"  Activation Date: {code.activation_date}\n")
                if code.redemption_date:
                    f.write(f"  Redemption Date: {code.redemption_date}\n")
                if code.expiration_date:
                    f.write(f"  Expiration Date: {code.expiration_date}\n")
                if code.recipient_name:
                    f.write(f"  Recipient: {code.recipient_name}\n")
                if code.company:
                    f.write(f"  Company: {code.company}\n")
                if code.payment_amount:
                    f.write(f"  Payment: {code.payment_method} ${code.payment_amount}\n")
                if code.notes:
                    f.write(f"  Notes: {code.notes}\n")
                f.write("\n")

    def add_code(self, code: FieldCode):
        """Add a new code to the ledger."""
        self._codes[code.code] = code
        self._save_ledger()

    def get_code(self, code: str) -> Optional[FieldCode]:
        """Get a code by its identifier."""
        return self._codes.get(code)

    def list_codes(self) -> List[FieldCode]:
        """List all codes."""
        return sorted(self._codes.values(), key=lambda c: c.code)

    def activate_code(self, code: str) -> bool:
        """
        Activate a code (Prometheus Activation).
        Only allowed if code is INACTIVE.
        Returns True if successful.
        """
        field_code = self._codes.get(code)
        if field_code is None:
            return False
        if field_code.status != CodeStatus.INACTIVE:
            return False
        field_code.status = CodeStatus.ACTIVE
        field_code.activation_date = datetime.utcnow().isoformat()
        self._save_ledger()
        return True

    def activate_range(self, start_code: str, end_code: str) -> int:
        """
        Activate a range of codes.
        Returns number of codes activated.
        """
        count = 0
        for code in sorted(self._codes.keys()):
            if start_code <= code <= end_code:
                if self.activate_code(code):
                    count += 1
        return count

    def deactivate_code(self, code: str) -> bool:
        """
        Deactivate a code (back to INACTIVE).
        Only allowed if code is ACTIVE and not REDEEMED.
        Returns True if successful.
        """
        field_code = self._codes.get(code)
        if field_code is None:
            return False
        if field_code.status != CodeStatus.ACTIVE:
            return False
        field_code.status = CodeStatus.INACTIVE
        field_code.activation_date = None
        self._save_ledger()
        return True

    def void_code(self, code: str, note: Optional[str] = None) -> bool:
        """
        Void a code (kill it completely).
        Returns True if successful.
        """
        field_code = self._codes.get(code)
        if field_code is None:
            return False
        field_code.status = CodeStatus.VOIDED
        if note:
            field_code.notes = (field_code.notes or "") + f"\nVOIDED: {note}"
        self._save_ledger()
        return True

    def mark_issued(
        self,
        code: str,
        name: str,
        company: Optional[str] = None,
        note: Optional[str] = None,
    ) -> bool:
        """Mark a code as issued to a recipient."""
        field_code = self._codes.get(code)
        if field_code is None:
            return False
        field_code.issue_type = IssueType.ISSUED
        field_code.recipient_name = name
        field_code.company = company
        if note:
            field_code.notes = (field_code.notes or "") + f"\nISSUED: {note}"
        self._save_ledger()
        return True

    def mark_sold(
        self,
        code: str,
        name: str,
        company: Optional[str] = None,
        payment_method: Optional[str] = None,
        amount: Optional[float] = None,
        note: Optional[str] = None,
    ) -> bool:
        """Mark a code as sold."""
        field_code = self._codes.get(code)
        if field_code is None:
            return False
        field_code.issue_type = IssueType.SOLD
        field_code.recipient_name = name
        field_code.company = company
        field_code.payment_method = payment_method
        field_code.payment_amount = amount
        if note:
            field_code.notes = (field_code.notes or "") + f"\nSOLD: {note}"
        self._save_ledger()
        return True

    def redeem_code(self, code: str) -> bool:
        """
        Redeem a code (customer uses it).
        Only allowed if code is ACTIVE.
        Returns True if successful.
        """
        field_code = self._codes.get(code)
        if field_code is None:
            return False
        if field_code.status != CodeStatus.ACTIVE:
            return False
        field_code.status = CodeStatus.REDEEMED
        field_code.redemption_date = datetime.utcnow().isoformat()
        # Set expiration based on tier
        if field_code.tier == CodeTier.TRIAL_7_DAY:
            # 7 days from redemption
            from datetime import timedelta
            exp_date = datetime.utcnow() + timedelta(days=7)
            field_code.expiration_date = exp_date.isoformat()
        elif field_code.tier == CodeTier.ENTERPRISE_EVAL:
            # 15 days from redemption
            from datetime import timedelta
            exp_date = datetime.utcnow() + timedelta(days=15)
            field_code.expiration_date = exp_date.isoformat()
        self._save_ledger()
        return True

    def generate_receipt(self, code: str) -> Optional[str]:
        """Generate a receipt for a sold code."""
        field_code = self._codes.get(code)
        if field_code is None:
            return None
        if field_code.issue_type != IssueType.SOLD:
            return None

        receipt_id = str(uuid.uuid4())[:8]
        receipt_filename = f"receipt_{code}_{receipt_id}.txt"
        receipt_path = self.receipts_folder / receipt_filename

        with open(receipt_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("AVERY LOGIC WORKS - COMMAND NEXUS\n")
            f.write("RECEIPT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Receipt ID: {receipt_id}\n")
            f.write(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write(f"Code: {code}\n")
            f.write(f"Label: {field_code.label}\n")
            f.write(f"Tier: {field_code.tier.value}\n\n")
            f.write(f"Recipient: {field_code.recipient_name}\n")
            if field_code.company:
                f.write(f"Company: {field_code.company}\n")
            f.write(f"\nPayment Method: {field_code.payment_method}\n")
            f.write(f"Amount: ${field_code.payment_amount}\n\n")
            f.write("Customer-facing license only.\n")
            f.write("Does not include source-code ownership, redistribution rights,\n")
            f.write("reverse-engineering rights, modification rights, licensing bypass\n")
            f.write("rights, or protected developer maintenance systems.\n\n")
            f.write("=" * 60 + "\n")
            f.write("Avery Logic Works\n")
            f.write("Website: AveryLogicWorks.com\n")
            f.write("Email: averylogicworks@gmail.com\n")
            f.write("=" * 60 + "\n")

        field_code.receipt_path = str(receipt_path)
        self._save_ledger()
        return str(receipt_path)

    def generate_one_code_file(self, code: str) -> Optional[str]:
        """Generate a one-code-per-file card for safe photography."""
        field_code = self._codes.get(code)
        if field_code is None:
            return None

        filename = f"{code}.txt"
        file_path = self.one_code_folder / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Avery Logic Works\n")
            f.write("Command Nexus\n\n")
            f.write("Code:\n")
            f.write(f"{code}\n\n")
            f.write("Tier:\n")
            f.write(f"{field_code.tier.value}\n\n")
            f.write("Status at creation:\n")
            f.write("Inactive until Avery Logic Works activates it.\n\n")
            f.write("Website:\n")
            f.write("AveryLogicWorks.com\n\n")
            f.write("Contact:\n")
            f.write("averylogicworks@gmail.com\n\n")
            f.write("Note:\n")
            f.write("Customer-facing license only. Does not include source-code ownership,\n")
            f.write("redistribution rights, reverse-engineering rights, modification rights,\n")
            f.write("licensing bypass rights, or protected developer maintenance systems.\n")

        return str(file_path)


def get_moirai_ledger() -> MoiraiLedger:
    """Get the singleton Moirai Ledger instance."""
    return MoiraiLedger()
