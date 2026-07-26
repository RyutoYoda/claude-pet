#!/bin/bash
set -euo pipefail

APP_NAME="Claude Pet"
VERSION="${1:-1.0.0}"
APP_DIR="dist/$APP_NAME.app"

echo "=== Building $APP_NAME v$VERSION ==="
rm -rf "$APP_DIR" dist/*.pkg

mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy Python package
cp -r claude_pet "$APP_DIR/Contents/Resources/"
cp -r assets "$APP_DIR/Contents/Resources/"
cp notify_hook.py "$APP_DIR/Contents/Resources/"

GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

cat > "$APP_DIR/Contents/MacOS/$APP_NAME" << LAUNCHER
#!/bin/bash
DIR="\$(cd "\$(dirname "\$0")/../Resources" && pwd)"
cd "\$DIR"
exec python3 -m claude_pet
LAUNCHER
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"

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

# Clean up metadata and cache files
find "$APP_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$APP_DIR" -name '._*' -delete 2>/dev/null || true
find "$APP_DIR" -name '.DS_Store' -delete 2>/dev/null || true

chmod -R u+w "$APP_DIR"
echo "=== .app bundle created ==="

pkgbuild \
    --root "$APP_DIR" \
    --identifier com.claude-pet.app \
    --version "$VERSION" \
    --install-location "/Applications/$APP_NAME.app" \
    "dist/$APP_NAME-$VERSION.pkg"
echo "=== .pkg created ==="
ls -lh "dist/$APP_NAME-$VERSION.pkg"
