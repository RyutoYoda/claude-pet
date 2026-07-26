#!/bin/bash
set -euo pipefail

APP_NAME="Claude Pet"
VERSION="${1:-1.0.0}"
APP_DIR="dist/$APP_NAME.app"

echo "=== Building $APP_NAME v$VERSION ==="
rm -rf dist

mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy Python package and assets
cp -r claude_pet "$APP_DIR/Contents/Resources/"
cp -r assets "$APP_DIR/Contents/Resources/"
cp notify_hook.py "$APP_DIR/Contents/Resources/"

# ── Bundle a self-contained Python venv ───────────────────────────────────
echo "=== Creating bundled venv ==="
BUNDLED_PYTHON="/usr/bin/python3"
if [ ! -x "$BUNDLED_PYTHON" ]; then
    BUNDLED_PYTHON=$(which python3)
fi
echo "Using Python: $BUNDLED_PYTHON ($("$BUNDLED_PYTHON" --version 2>&1))"

VENV_DIR="$APP_DIR/Contents/Resources/venv"
"$BUNDLED_PYTHON" -m venv "$VENV_DIR"

# Install dependencies into the venv
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet \
    pyobjc-core \
    pyobjc-framework-Cocoa \
    pyobjc-framework-Quartz

# Strip bytecode and clean up
find "$VENV_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$VENV_DIR" -name '*.pyc' -delete 2>/dev/null || true
rm -rf "$VENV_DIR/include" 2>/dev/null || true
rm -rf "$VENV_DIR/lib/python3."*/test 2>/dev/null || true
rm -rf "$VENV_DIR/lib/python3."*/site-packages/pip* 2>/dev/null || true
rm -rf "$VENV_DIR/lib/python3."*/site-packages/setuptools* 2>/dev/null || true
# Keep only the site-packages with installed deps
echo "=== Venv size ==="
du -sh "$VENV_DIR"

# ── Launcher ──────────────────────────────────────────────────────────────
cat > "$APP_DIR/Contents/MacOS/$APP_NAME" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
export PYTHONHOME="$DIR/venv"
export PATH="$DIR/venv/bin:/usr/bin:/bin"
cd "$DIR"
exec "$DIR/venv/bin/python3" -m claude_pet
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

# ── Build component pkg ───────────────────────────────────────────────────
COMPONENT_PKG="dist/Claude-Pet-${VERSION}.pkg"
pkgbuild \
    --root "$APP_DIR" \
    --identifier com.claude-pet.app \
    --version "$VERSION" \
    --install-location "/Applications/$APP_NAME.app" \
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
