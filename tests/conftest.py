"""Pytest configuration ensuring legacy names are available for tests."""

import os
import sys

# Ensure project root is on the path for direct module imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import enhanced modules so their builtins shims are registered
import player.enhanced_skills  # noqa: F401,E402
import mechanics.enhanced_combat  # noqa: F401,E402
import mechanics.combat_integration  # noqa: F401,E402

