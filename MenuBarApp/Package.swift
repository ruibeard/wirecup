// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "WirecupBar",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "WirecupBar",
            path: "Sources/WirecupBar"
        )
    ]
)
