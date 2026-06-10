# Command Nexus License System

## Overview

The Command Nexus license system enforces subscription tiers at runtime. It consists of three components:

1. **License Manager** (`src/core/license_manager.py`) — embedded in the app, validates keys, enforces limits
2. **License Dialog** (`src/core/license_dialog.py`) — shown on startup when no valid license exists
3. **Key Generator** (`tools/license_key_generator.py`) — standalone tool YOU run to generate keys for customers

---

## Subscription Tiers

| Tier | Price | AIs | Duration | Key Prefix |
|------|-------|-----|----------|------------|
| **Trial** | $10 one-time | 1 | 15 days | `TR` |
| **Starter** | $20/month | 2 | 30 days | `ST` |
| **Pro** | $30/month | 4 | 30 days | `PR` |
| **Annual** | $50/year | 5 | 365 days | `AN` |
| **Unlimited** | $80/month | Unlimited | 30 days | `UN` |

---

## How It Works

### For Users (In the App)

1. Download and open Command Nexus
2. If no license: shown the License Activation Dialog
3. Options:
   - **Enter a key** — activates the app with that tier's features
   - **Continue in Demo Mode** — browse the UI but cannot create/deploy AIs
4. Once activated: window title shows tier and days remaining

### For You (Key Generation)

Run the generator tool:

```bash
# Generate 1 trial key (15 days)
python tools/license_key_generator.py --tier trial --days 15 --count 1

# Generate 5 starter keys (30 days)
python tools/license_key_generator.py --tier starter --days 30 --count 5

# Generate 1 unlimited key (30 days)
python tools/license_key_generator.py --tier unlimited --days 30 --count 1

# Verify an existing key
python tools/license_key_generator.py --verify TR00-XXXX-XXXX-XXXX-XXXX
```

Keys are saved to `tools/generated_keys/` for your records.

---

## Enforcement Points

The license system enforces limits at these points:

1. **AI Forge — Create AI** (`_on_ai_saved`)
   - Demo mode: blocked
   - Over limit: blocked with upgrade message

2. **AI Forge — Deploy AI** (`_activate_selected`)
   - Same enforcement as creation

3. **AI Forge — Drop-In AI** (`_drop_in_ai`)
   - Same enforcement as creation

4. **Starter AIs**
   - Pre-built starter AIs (Lily, Daedalus, Hermes, etc.) do NOT count against user limits
   - Only user-created/imported AIs count

---

## Demo Mode Behavior

When no valid license is active:

- **Can do:** Browse all windows, view starter AIs, read Books, explore capabilities
- **Cannot do:** Create new AIs, deploy AIs, drop-in AIs, save configurations
- **Visual indicator:** Window title shows `[DEMO — Limited]`

---

## Test Keys (Generated)

See these files for pre-generated test keys:
- `test_keys.json` — Trial keys
- `test_keys_starter.json` — Starter keys
- `test_keys_pro.json` — Pro keys
- `test_keys_annual.json` — Annual keys
- `test_keys_unlimited.json` — Unlimited keys

---

## File Locations

| Component | Path |
|-----------|------|
| License Manager | `src/core/license_manager.py` |
| License Dialog | `src/core/license_dialog.py` |
| Key Generator | `tools/license_key_generator.py` |
| License Storage | `~/.command_nexus/license.json` |
| Generated Keys | `tools/generated_keys/*.json` |

---

## Security Notes

- Keys use HMAC-SHA256 signatures — cannot be forged without the secret
- The secret is embedded in both the app and generator (must match)
- Keys are 40-character hex strings with dashes for readability
- Each key is single-use (stored on activation, but same key can be re-entered on same machine)
- For production, consider using asymmetric cryptography (Ed25519) or a keyserver

---

## Next Steps

1. Test the system with the generated test keys
2. Set up a payment processor (Stripe, Paddle) to sell keys
3. Build a web page where customers enter email + pay → receive key via email
4. Consider adding key revocation/deactivation for refunds/fraud
