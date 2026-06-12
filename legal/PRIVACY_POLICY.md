# COMMAND NEXUS — PRIVACY POLICY

**Effective Date:** June 10, 2026  
**Company:** Pantheon Forge LLC

---

## 1. OUR COMMITMENT

Command Nexus is **local-first and privacy-first**. Your data stays on your machine. We do not operate cloud AI backends, do not collect prompts, and do not train models on your usage.

## 2. WHAT WE COLLECT

### 2.1 Automatically (minimal)
- License tier and activation status (for validation)
- Anonymous crash logs (opt-in only)
- Basic telemetry: app version, OS type, feature usage counts

### 2.2 What We DO NOT Collect
- Your AI prompts or conversations
- File contents processed by the Software
- Personal identity information (unless voluntarily provided for support)
- Book/AI configuration data (stored locally only)

## 3. HOW DATA IS USED

- License validation against our key server (key only, no personal data)
- Anonymous telemetry to improve the Software
- Crash diagnostics (only if you opt in)

## 4. DATA STORAGE

All AI configurations, Books, audit logs, and settings are stored **locally** in:
```
~/.command_nexus/
```

Nothing is uploaded to Pantheon Forge servers except:
- License key validation requests
- Opt-in anonymous telemetry

## 5. THIRD PARTIES

We do not sell, rent, or share your data with third parties for marketing.

If you choose to connect the Software to external LLM APIs (e.g., OpenAI, Anthropic), your prompts are sent directly to those providers under their privacy policies. Pantheon Forge LLC is not responsible for their handling of data.

## 6. SECURITY

We employ industry-standard measures:
- License keys use HMAC-SHA256 cryptographic signing
- Anti-tamper protections prevent unauthorized modification
- All local data is stored in plain JSON (not encrypted by default; user may enable at own risk)

## 7. YOUR RIGHTS

You may:
- Request deletion of any account data we hold
- Disable telemetry at any time in Settings
- Export your local data for portability

## 8. CONTACT

**Privacy Officer:** privacy@pantheonforge.io

---

*This Privacy Policy may be updated. Continued use constitutes acceptance.*
