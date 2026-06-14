from enum import Enum, auto


class SpeedLevel(Enum):
    REGULAR = "Regular"
    MODERATE = "Moderate"
    FAST = "Fast"


class UseCaseClass(Enum):
    INDIVIDUAL = "Individual"
    EDUCATIONAL = "Educational"
    TASK_READY = "Task-Ready"
    BUSINESS = "Business"
    ENTERPRISE = "Enterprise"
    ALL_ROUNDER = "All-Rounder"
    MILITARY_GOVERNMENT = "Military / Government"


class PresenceState(Enum):
    IDLE = "IDLE"
    THINKING = "THINKING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RUNNING_MISSION = "RUNNING_MISSION"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    DEMO_MODE = "DEMO_MODE"
    BACKEND_NOT_CONNECTED = "BACKEND_NOT_CONNECTED"


class ResourceGrade(Enum):
    GREEN = "green"
    GREEN_YELLOW = "green_yellow"
    YELLOW = "yellow"
    YELLOW_RED = "yellow_red"
    RED = "red"
    CRIMSON_RED = "crimson_red"


DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_VIEWPORT_FPS_REGULAR = 2
DEFAULT_VIEWPORT_FPS_MODERATE = 10
DEFAULT_VIEWPORT_FPS_FAST = 30

AUDIT_PANE_MAX_LINES = 1000

PROPRIETARY_NOTICE = (
    "Command Nexus™ â€” PROPRIETARY AND CONFIDENTIAL\n"
    "Unauthorized use, reproduction, or distribution is strictly prohibited.\n"
    "All rights reserved.\n"
)
