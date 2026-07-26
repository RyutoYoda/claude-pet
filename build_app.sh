#!/bin/bash
set -euo pipefail

APP_NAME="Claude Pet"
VERSION="${1:-1.0.0}"
APP_DIR="dist/$APP_NAME.app"

echo "=== Building $APP_NAME v$VERSION ==="
rm -rf dist

mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy Python package and assets (no bundled deps — installed via postinstall)
cp -r claude_pet "$APP_DIR/Contents/Resources/"
cp -r assets "$APP_DIR/Contents/Resources/"
cp notify_hook.py "$APP_DIR/Contents/Resources/"
cp permission_hook.py "$APP_DIR/Contents/Resources/"

# ── Launcher (uses system python3 + PYTHONPATH) ──────────────────────────
cat > "$APP_DIR/Contents/MacOS/$APP_NAME" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
SITE_PKG="$DIR/site-packages"
USER_SITE_PKG="$HOME/.local/share/claude-pet/site-packages"

# Resolve Python: prefer the one recorded at install time
if [ -f "$SITE_PKG/.python_path" ]; then
    PYTHON=$(cat "$SITE_PKG/.python_path")
elif [ -f "$USER_SITE_PKG/.python_path" ]; then
    PYTHON=$(cat "$USER_SITE_PKG/.python_path")
else
    PYTHON="/usr/bin/python3"
fi
[ -x "$PYTHON" ] || PYTHON="/usr/bin/python3"

# On first launch, dependencies may not be installed yet
if [ ! -f "$SITE_PKG/AppKit/__init__.py" ] && [ ! -f "$USER_SITE_PKG/AppKit/__init__.py" ]; then
    echo "Claude Pet: Installing dependencies (one-time setup)..."
    PYTHON=""
    for p in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
        if [ -x "$p" ]; then
            VER=$("$p" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            MAJ=$(echo "$VER" | cut -d. -f1)
            MIN=$(echo "$VER" | cut -d. -f2)
            if [ "$MAJ" = "3" ] && [ "$MIN" -ge 10 ] 2>/dev/null; then
                PYTHON="$p"
                break
            fi
        fi
    done
    if [ -z "$PYTHON" ]; then
        osascript -e 'display dialog "Claude Pet には Python 3.10 以降が必要です。\nHomebrew で: brew install python" buttons {"OK"} default button 1'
        exit 1
    fi
    # Install to user-writable location (works without root)
    mkdir -p "$USER_SITE_PKG"
    "$PYTHON" -m pip install --quiet --no-warn-script-location --target "$USER_SITE_PKG" \
        pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz
    find "$USER_SITE_PKG" -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
    find "$USER_SITE_PKG" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    echo "$PYTHON" > "$USER_SITE_PKG/.python_path"
    echo "Claude Pet: Dependencies ready"
fi

export PYTHONPATH="$SITE_PKG:$USER_SITE_PKG:$DIR"
cd "$DIR"
exec "$PYTHON" "$DIR/claude_pet/__main__.py"
LAUNCHER
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"

# ── Info.plist ────────────────────────────────────────────────────────────
cat > "$APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleExecutable</key>
	<string>$APP_NAME</string>
	<key>CFBundleIdentifier</key>
	<string>com.claude-pet.app</string>
	<key>CFBundleName</key>
	<string>$APP_NAME</string>
	<key>CFBundleDisplayName</key>
	<string>$APP_NAME</string>
	<key>CFBundleVersion</key>
	<string>$VERSION</string>
	<key>CFBundleShortVersionString</key>
	<string>$VERSION</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>LSUIElement</key>
	<true/>
	<key>NSHighResolutionCapable</key>
	<true/>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
</dict>
</plist>
PLIST

# Clean metadata files
find "$APP_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$APP_DIR" -name '._*' -delete 2>/dev/null || true
find "$APP_DIR" -name '.DS_Store' -delete 2>/dev/null || true
chmod -R u+w "$APP_DIR"

echo "=== .app bundle created ==="
du -sh "$APP_DIR"

# ── Build component pkg with postinstall script ──────────────────────────
chmod +x installer_resources/scripts/postinstall

COMPONENT_PKG="dist/Claude-Pet-${VERSION}.pkg"
pkgbuild \
    --root "$APP_DIR" \
    --identifier com.claude-pet.app \
    --version "$VERSION" \
    --install-location "/Applications/$APP_NAME.app" \
    --scripts installer_resources/scripts \
    "$COMPONENT_PKG"

# ── Build distribution pkg (with installer UI) ────────────────────────────
DIST_PKG="dist/Claude-Pet-${VERSION}-installer.pkg"
cp installer_resources/Distribution.xml /tmp/Distribution-${VERSION}.xml
sed -i '' "s/#VERSION#/$VERSION/g" /tmp/Distribution-${VERSION}.xml
productbuild \
    --distribution /tmp/Distribution-${VERSION}.xml \
    --package-path dist \
    --resources installer_resources \
    "$DIST_PKG"

# Clean up intermediate files
rm -f "$COMPONENT_PKG"

echo "=== Done ==="
ls -lh "$DIST_PKG"
