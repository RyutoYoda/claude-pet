"""Build script for py2app.

Usage:
    python setup.py py2app
"""
import sys

from setuptools import setup
from setuptools._distutils.core import setup as _orig_setup

# py2app refuses to work if install_requires is set (reads from pyproject.toml).
# Override setup to clear it before py2app command runs.

_orig_call = setup


def _setup(**attrs):
    if "py2app" in sys.argv:
        attrs.pop("install_requires", None)
        dist = _orig_setup(**attrs)
        dist.install_requires = []
        return dist
    return _orig_setup(**attrs)


import builtins as _b
_b.setup = _setup

# Now import py2app after the override
from py2app.build_app import py2app  # noqa: E402, F401

_b.setup = _orig_setup

# ── Normal setup call ──────────────────────────────────────────────────────

APP = ["run_pet.py"]
DATA_FILES = [("assets", ["assets/pet.png"])]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["claude_pet"],
    "includes": [
        "objc",
        "AppKit",
        "Foundation",
        "Quartz",
    ],
    "plist": {
        "CFBundleName": "Claude Pet",
        "CFBundleDisplayName": "Claude Pet",
        "CFBundleIdentifier": "com.claude-pet.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSUIElement": True,
    },
}

setup(
    name="Claude Pet",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)
