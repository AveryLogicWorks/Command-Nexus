"""
Avatar video configuration for Command Nexus.
Edit these paths to point to your video assets.
"""
from pathlib import Path

# Folder containing avatar video assets
AVATAR_VIDEO_DIR = Path("B:/Videos/1# AI modal 3D moveing speaking modle")

# Explicit file mappings — adjust these if you want different files assigned
IDLE_VIDEO_PATH = AVATAR_VIDEO_DIR / "High_resolution_and_she_should.mp4"
TALKING_VIDEO_PATH = AVATAR_VIDEO_DIR / "I_need_another_one_I_like_it_.mp4"
TALKING_VIDEO_ALT_PATH = AVATAR_VIDEO_DIR / "I_need_you_to_make_these_imag.mp4"

# Static idle image fallback (optional)
IDLE_IMAGE_PATH = None  # e.g., Path(".../idle.png")

# Validate on import (silent — just for reference)
_VIDEO_FILES = [IDLE_VIDEO_PATH, TALKING_VIDEO_PATH, TALKING_VIDEO_ALT_PATH]


def get_avatar_assets():
    """
    Return a dict of existing avatar asset paths for use in AIAvatarWidget.
    Only includes paths that actually exist on disk.
    """
    assets = {}
    if IDLE_VIDEO_PATH.exists():
        assets["idle_video"] = str(IDLE_VIDEO_PATH)
    if TALKING_VIDEO_PATH.exists():
        assets["talking_video"] = str(TALKING_VIDEO_PATH)
    if IDLE_IMAGE_PATH and IDLE_IMAGE_PATH.exists():
        assets["idle_image"] = str(IDLE_IMAGE_PATH)
    return assets
