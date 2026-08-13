#!/usr/bin/env bash
set -euo pipefail

# Build wirecup as standalone Mach-O binary
echo "Building wirecup..."
source .venv/bin/activate && pyinstaller wirecup.spec --noconfirm --distpath dist
echo "Building WirecupBar menu bar app..."
( cd MenuBarApp && swift build -c release )

# Package as proper .app bundle so it launches without a Terminal window
# Support both Apple Silicon and Intel Macs
if [ -d "MenuBarApp/.build/arm64-apple-macosx/release" ]; then
  BINARY="MenuBarApp/.build/arm64-apple-macosx/release/WirecupBar"
  APP="MenuBarApp/.build/arm64-apple-macosx/release/WirecupBar.app"
else
  BINARY="MenuBarApp/.build/release/WirecupBar"
  APP="MenuBarApp/.build/release/WirecupBar.app"
fi

mkdir -p "$APP/Contents/MacOS"
cp "$BINARY" "$APP/Contents/MacOS/"

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>WirecupBar</string>
    <key>CFBundleIdentifier</key>
    <string>dev.ruibeard.wirecupbar</string>
    <key>CFBundleName</key>
    <string>WirecupBar</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSBackgroundOnly</key>
    <true/>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "Done: dist/wirecup + MenuBarApp/.build/release/WirecupBar.app"
