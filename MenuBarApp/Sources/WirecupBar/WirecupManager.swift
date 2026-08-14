import SwiftUI
import AppKit

struct ProjectItem: Identifiable {
    let id = UUID()
    let name: String
    let path: String
}

class WirecupManager: ObservableObject {
    @Published var isRunning = false
    @Published var statusText = "Ready"
    @Published var url = "http://localhost:8765/"
    @Published var currentProjectName = ""
    @Published var projectPath: String {
        didSet { UserDefaults.standard.set(projectPath, forKey: Keys.projectPath) }
    }
    @Published var wirecupBinaryPath: String {
        didSet { UserDefaults.standard.set(wirecupBinaryPath, forKey: Keys.wirecupBinaryPath) }
    }
    @Published var rootFolder: String {
        didSet { UserDefaults.standard.set(rootFolder, forKey: Keys.rootFolder) }
    }
    @Published var searchQuery = ""
    @Published var projects: [ProjectItem] = []
    @Published var showSettings = false
    @Published var customPort: String {
        didSet { UserDefaults.standard.set(customPort, forKey: Keys.customPort) }
    }

    var filteredProjects: [ProjectItem] {
        if searchQuery.isEmpty { return projects }
        return projects.filter { $0.name.localizedCaseInsensitiveContains(searchQuery) }
    }

    var displayRootFolder: String {
        (rootFolder as NSString).expandingTildeInPath
    }

    private var process: Process?

    var effectivePort: Int {
        Int(customPort) ?? 8765
    }

    private enum Keys {
        static let projectPath = "projectPath"
        static let wirecupBinaryPath = "wirecupBinaryPath"
        static let rootFolder = "rootFolder"
        static let customPort = "customPort"
    }

    init() {
        projectPath = UserDefaults.standard.string(forKey: Keys.projectPath) ?? ""
        let saved = UserDefaults.standard.string(forKey: Keys.wirecupBinaryPath) ?? ""
        wirecupBinaryPath = saved
        rootFolder = UserDefaults.standard.string(forKey: Keys.rootFolder) ?? "~/code"
        customPort = UserDefaults.standard.string(forKey: Keys.customPort) ?? "8765"

        if wirecupBinaryPath.isEmpty {
            wirecupBinaryPath = findWirecupBinary() ?? ""
        }

        NotificationCenter.default.addObserver(
            forName: NSApplication.willTerminateNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.stop()
        }

        scanProjects()
    }

    deinit {
        stop()
    }

    private func findWirecupBinary() -> String? {
        let candidates = [
            "~/.wirecup/wirecup",
            "~/wirecup",
            "/usr/local/bin/wirecup",
            "/opt/homebrew/bin/wirecup",
        ]

        // Check relative to the app bundle
        let bundleURL = URL(fileURLWithPath: Bundle.main.bundlePath)
        let distURL = bundleURL
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("dist")
            .appendingPathComponent("wirecup")

        var pathsToCheck = candidates
        pathsToCheck.append(distURL.path)

        for path in pathsToCheck {
            let expanded = (path as NSString).expandingTildeInPath
            if FileManager.default.fileExists(atPath: expanded) {
                return expanded
            }
        }

        // Try which
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        task.arguments = ["which", "wirecup"]
        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = Pipe()
        do {
            try task.run()
            task.waitUntilExit()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let path = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines)
            return path?.isEmpty == false ? path : nil
        } catch {
            return nil
        }
    }

    func scanProjects() {
        guard !rootFolder.isEmpty else {
            projects = []
            return
        }
        let expanded = (rootFolder as NSString).expandingTildeInPath
        let root = URL(fileURLWithPath: expanded)
        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: root,
            includingPropertiesForKeys: [.isDirectoryKey],
            options: [.skipsHiddenFiles]
        ) else {
            projects = []
            return
        }
        projects = contents
            .filter { url in
                (try? url.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) == true
            }
            .filter { url in
                let cupDir = url.appendingPathComponent(".wirecup")
                return FileManager.default.fileExists(atPath: cupDir.path)
            }
            .map { url in
                ProjectItem(name: url.lastPathComponent, path: url.path)
            }
            .sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
    }

    func start(project: ProjectItem) {
        guard !isRunning else { return }
        projectPath = project.path
        currentProjectName = project.name
        start()
    }

    func start() {
        guard !isRunning else { return }
        guard !projectPath.isEmpty else {
            statusText = "No project selected"
            return
        }

        if wirecupBinaryPath.isEmpty {
            statusText = "Wirecup binary not found — click 'Locate Wirecup Binary...'"
            return
        }

        let binaryPath = wirecupBinaryPath
        if !FileManager.default.fileExists(atPath: binaryPath) {
            statusText = "Wirecup binary missing at \(binaryPath)"
            return
        }

        let expandedPath = (projectPath as NSString).expandingTildeInPath
        var isDir: ObjCBool = false
        if !FileManager.default.fileExists(atPath: expandedPath, isDirectory: &isDir) || !isDir.boolValue {
            statusText = "Project path invalid"
            return
        }

        stop()

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: binaryPath)
        proc.arguments = [expandedPath, "--port", "\(effectivePort)", "--no-browser"]
        proc.currentDirectoryURL = URL(fileURLWithPath: expandedPath)

        proc.terminationHandler = { [weak self] proc in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.isRunning = false
                self.statusText = proc.terminationReason == .uncaughtSignal
                    ? "Crashed"
                    : "Stopped"
                self.process = nil
            }
        }

        do {
            try proc.run()
            process = proc
            statusText = "Starting \(currentProjectName)..."

            pollApiReady()
        } catch {
            statusText = "Failed: \(error.localizedDescription)"
        }
    }

    private func pollApiReady(attempt: Int = 0) {
        guard process?.isRunning == true else { return }

        let url = URL(string: "http://localhost:\(effectivePort)/api/ready")!
        var request = URLRequest(url: url)
        request.timeoutInterval = 1.0

        URLSession.shared.dataTask(with: request) { [weak self] data, _, _ in
            guard let self = self else { return }

            if let data = data,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               json["ready"] as? Bool == true {
                DispatchQueue.main.async {
                    self.isRunning = true
                    self.statusText = "\(self.currentProjectName) — port \(self.effectivePort)"
                    self.url = "http://localhost:\(self.effectivePort)/"
                    self.openPreview()
                }
                return
            }

            if attempt < 50 {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                    self.pollApiReady(attempt: attempt + 1)
                }
            } else {
                DispatchQueue.main.async {
                    self.statusText = "Did not come up"
                    self.stop()
                }
            }
        }.resume()
    }

    func stop() {
        if let proc = process, proc.isRunning {
            proc.terminationHandler = nil
            proc.terminate()
        }
        process = nil
        let killer = Process()
        killer.executableURL = URL(fileURLWithPath: "/usr/bin/pkill")
        killer.arguments = ["-f", "wirecup.*--port \(effectivePort)"]
        try? killer.run()
        killer.waitUntilExit()
        isRunning = false
        statusText = "Stopped"
    }

    func openPreview() {
        guard let url = URL(string: url) else { return }
        NSWorkspace.shared.open(url)
    }

    func chooseRootFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.message = "Choose the folder containing your projects"

        let expanded = (rootFolder as NSString).expandingTildeInPath
        if FileManager.default.fileExists(atPath: expanded) {
            panel.directoryURL = URL(fileURLWithPath: expanded)
        }

        if panel.runModal() == .OK, let url = panel.url {
            let home = FileManager.default.homeDirectoryForCurrentUser.path
            if url.path.hasPrefix(home) {
                rootFolder = "~" + url.path.dropFirst(home.count)
            } else {
                rootFolder = url.path
            }
            scanProjects()
        }
    }

    func chooseWirecupBinary() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.message = "Locate the wirecup binary"

        if panel.runModal() == .OK, let url = panel.url {
            wirecupBinaryPath = url.path
            statusText = "Binary set to \(url.lastPathComponent)"
        }
    }
}
