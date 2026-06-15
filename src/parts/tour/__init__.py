"""
Command Nexus™ Tour System
===========================
Interactive hands-on tutorials for new users.
"""
from .interactive_tour import (
    InteractiveTourController,
    start_interactive_tour,
    TourTooltip,
    TourOverlay,
    get_test_license_keys,
)
from .guided_tour import (
    GuidedTourDialog,
    show_guided_tour,
    TourStep,
)
from .demo_tour import (
    DemoTourController,
    DemoTourTooltip,
    DemoTourOverlay,
    DemoTourStep,
    start_demo_tour,
)

__all__ = [
    # Interactive Tour
    "InteractiveTourController",
    "start_interactive_tour",
    "TourTooltip",
    "TourOverlay",
    "get_test_license_keys",
    # Demo Tour (recommended)
    "DemoTourController",
    "start_demo_tour",
    "DemoTourTooltip",
    "DemoTourOverlay",
    "DemoTourStep",
    # Legacy
    "GuidedTourDialog",
    "show_guided_tour",
    "TourStep",
]
