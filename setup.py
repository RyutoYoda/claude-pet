from setuptools import setup

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
