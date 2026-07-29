from pathlib import Path
import shutil

ROOT = Path.cwd()
RAW_LEN = 36
HMAC_LEN = 16

SKIP = {".git", ".venv", "venv", "__pycache__", "dist", "build", "site-packages"}

REPLACEMENTS = {
    "len(key) != 36": "len(key) != 36",
    "len(raw) > 36": "len(raw) > 36",
    "raw = raw[:36]": "raw = raw[:36]",
    "key[20:36]": "key[20:36]",
    "hmac_part = key[20:36]": "hmac_part = key[20:36]",
    "hexdigest()[:16].upper()": "hexdigest()[:16].upper()",
    "hexdigest()[:16]": "hexdigest()[:16]",
    "Expected 36 characters.": "Expected 36 characters.",
    "Expected 36 characters.": "Expected 36 characters.",
    "Expected 36 characters": "Expected 36 characters",
    "36-character license key": "36-character license key",
    "36-character core key": "36-character core key",
    "36-char hex license key": "36-char hex license key",
    "36-char raw key": "36-char raw key",
    "9 groups of 4": "9 groups of 4",
    "hmac(16)": "hmac(16)",
}

def skip_path(path: Path) -> bool:
    return any(part.lower() in SKIP for part in path.parts)

def likely_license_file(path: Path, text: str) -> bool:
    low = str(path).lower()
    return (
        "license" in low
        or "activation" in low
        or "generate_trial_key" in low
        or "generate_field_codes" in low
        or "Expected 36 characters" in text
        or "hmac_part = key[20:36]" in text
        or "hexdigest()[:16]" in text
    )

changed = []

for path in ROOT.rglob("*.py"):
    if skip_path(path):
        continue

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue

    if not likely_license_file(path, text):
        continue

    new = text
    for old, repl in REPLACEMENTS.items():
        new = new.replace(old, repl)

    if new != text:
        backup = path.with_suffix(path.suffix + ".license36_backup")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(new, encoding="utf-8")
        changed.append(str(path.relative_to(ROOT)))

print("LICENSE KEY RAW LENGTH FIX: 36")
print("Changed files:")
for item in changed:
    print(" -", item)

if not changed:
    print("No files changed. The active file may already be patched or may be outside this folder.")
