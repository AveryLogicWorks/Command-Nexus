# Command Nexus™ — Key Generator Suite
## Avery Logic Works™ — Proprietary and Confidential

This folder contains **standalone key generators** separated from the main Command Nexus™ program.

**Every `.bat` file opens the same unified GUI.** Pick your key type, set params, click Generate.

---

## Quick Start

Double-click **any** `.bat` file — they all open the same GUI:

```powershell
A:\Command_Nexus_Keys> keygen_gui.bat
```

Or run the GUI directly:

```powershell
cd "A:\Command_Nexus_Keys"
py -3.12 keygen_gui.py
```

---

## What the Crypto Key Is For

`nexus_crypto.py` contains the **shared secrets** that the main Command Nexus™ app uses to validate keys:

- `_SECRET_KEY` — Public-tier salt (Trial, Starter, Pro, Business, Unlimited)
- `_INTERNAL_SALT` — Employee forever-unlock salt
- `_FOUNDER_SALT` — Founder absolute / GOD MODE salt

These salts **must** match `src/core/license_manager.py` in the main app. If they diverge, keys generated here will be rejected by the app.

---

## GUI Layout

### Generate Tab
- **Key Type dropdown**: Internal, Founder, Trial, Starter, Pro, Business, Unlimited
- **Dynamic fields** change based on selection:
  - Internal → Email, Employee ID
  - Founder → Contract ID, Notes
  - Trial → Days, Notes
  - Paid → Subscription Months
- **Quantity** spinner (default 1)
- **Generate** button — creates keys only when you click it
- **Output** pane with Copy / Save JSON buttons

### Validate Tab
- Paste any number of keys (one per line)
- Click **Validate** to check tier, expiry, and HMAC signature

---

## Key Types

| Type | Tier Code | Salt | Expiry | Purpose |
|------|-----------|------|--------|---------|
| **Internal** | `NI` | `_INTERNAL_SALT` | 2099 | Avery Logic Works™ employees |
| **Founder** | `FD` | `_FOUNDER_SALT` | 2099 | Founder absolute / GOD MODE |
| **Trial** | `TR` | `_SECRET_KEY` | 7 days | Public demos, events |
| **Starter** | `ST` | `_SECRET_KEY` | 30 days | $20/mo — 2 AIs |
| **Pro** | `PR` | `_SECRET_KEY` | 30 days | $30/mo — 4 AIs |
| **Business** | `BU` | `_SECRET_KEY` | 30 days | $50/mo — 5 AIs |
| **Unlimited** | `UN` | `_SECRET_KEY` | 30 days | $80/mo — Unlimited AIs |

---

## File Layout

```
A:\Command_Nexus_Keys\
├── nexus_crypto.py              # Shared crypto (salts, HMAC, validation)
├── generate_internal_key.py     # CLI: Internal employee keys
├── generate_internal_key.bat    # → Opens GUI
├── generate_founder_key.py      # CLI: Founder absolute keys
├── generate_founder_key.bat     # → Opens GUI
├── generate_trial_key.py        # CLI: Trial keys
├── generate_trial_key.bat       # → Opens GUI
├── generate_paid_key.py         # CLI: Paid subscription keys
├── generate_paid_key.bat        # → Opens GUI
├── keygen_gui.py                # Unified PyQt6 GUI (all generators + validator)
├── keygen_gui.bat               # → Opens GUI
└── README.md                    # This file
```

---

## CLI Usage (Advanced)

If you prefer the command line, the `.py` files still work directly:

```powershell
# Internal (employee) keys — forever unlock
py generate_internal_key.py --qty 5 --email dev@averylogicworks.com

# Founder keys — GOD MODE
py generate_founder_key.py --qty 1 --contract FNDR-2026-001

# Trial keys — 7-day free
py generate_trial_key.py --qty 10 --days 7 --notes "Tech Expo"

# Paid keys — Starter, Pro, Business, Unlimited
py generate_paid_key.py --tier pro --months 12 --qty 1
```

---

## Validating Keys Programmatically

```python
from nexus_crypto import validate_key

result = validate_key("TR1234567890ABCDEF01...")
# result = {"valid": True, "tier": "trial", "expired": False, ...}
```

---

## ⚠️ Security Notes

- **Founder keys** bypass ALL protections. Treat them like nuclear launch codes.
- **Internal keys** are forever-unlock. Only issue to verified employees.
- **Trial keys** are public — hand them out freely at events.
- **Paid keys** are revenue — track them in your billing system.
- All keys use the same 40-char hex format: `TIER(2) + EXPIRY(10) + RANDOM(8) + HMAC(20)`

---

## Requirements

- Python 3.10+
- For GUI: `py -3.12 -m pip install PyQt6`

---

*Avery Logic Works™ — Command Nexus™ — All Rights Reserved*
