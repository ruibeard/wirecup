#!/usr/bin/env bash
set -euo pipefail

# Build wirecup as standalone Mach-O binary
echo "Building wirecup..."
source .venv/bin/activate && pyinstaller wirecup.spec --noconfirm --distpath dist
echo "Building WirecupBar menu bar app..."
( cd MenuBarApp && swift build -c release )

# Package as a proper .app bundle so it launches without a Terminal window,
# and install it to /Applications so it survives `.build` being wiped.
BINARY="$(cd MenuBarApp && swift build -c release --show-bin-path)/WirecupBar"
APP="/Applications/WirecupBar.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cp "$BINARY" "$APP/Contents/MacOS/"
codesign --force --sign - "$APP"

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

echo "Done: dist/wirecup + /Applications/WirecupBar.app"
