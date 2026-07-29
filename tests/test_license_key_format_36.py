from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _normalized(key: str) -> str:
    return "".join(ch for ch in key if ch.isalnum())


def test_root_license_generator_outputs_36_character_keys():
    root = Path(__file__).resolve().parents[1]
    mod = _load_module(root / "license_key_generator.py", "root_license_key_generator")

    for tier in mod.SubscriptionTier:
        record = mod.generate_license_key(tier)
        key = record["key"]
        raw = _normalized(key)

        assert len(raw) == 36
        assert len(key) == 44
        assert not key.endswith("-")
        assert mod.verify_key(key)["valid"] is True


def test_tools_license_generator_outputs_36_character_keys_without_trailing_dash():
    root = Path(__file__).resolve().parents[1]
    mod = _load_module(root / "tools" / "license_key_generator.py", "tools_license_key_generator")

    for tier in mod.SubscriptionTier:
        key = mod.generate_key(tier, 30)
        raw = _normalized(key)
        valid, tier_name, _ = mod.validate_generated_key(key)

        assert len(raw) == 36
        assert len(key) == 44
        assert not key.endswith("-")
        assert valid is True
        assert tier_name == tier.value
