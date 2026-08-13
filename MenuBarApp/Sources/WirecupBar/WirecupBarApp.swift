import SwiftUI

@main
struct WirecupBarApp: App {
    @StateObject private var manager = WirecupManager()

    init() {
        NSApplication.shared.setActivationPolicy(.accessory)
    }

    var body: some Scene {
        MenuBarExtra {
            VStack(alignment: .leading, spacing: 0) {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                    TextField("Filter projects...", text: $manager.searchQuery)
                        .textFieldStyle(.plain)
                        .font(.system(size: 12))
                    if !manager.searchQuery.isEmpty {
                        Button(action: { manager.searchQuery = "" }) {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 10))
                        }
                        .buttonStyle(.plain)
                        .foregroundColor(.secondary)
                    }
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(Color.primary.opacity(0.06))
                .cornerRadius(6)
                .padding(.horizontal, 10)
                .padding(.top, 8)
                .padding(.bottom, 4)

                if !manager.rootFolder.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "folder")
                            .font(.system(size: 9))
                        Text(manager.displayRootFolder)
                            .lineLimit(1)
                            .truncationMode(.middle)
                    }
                    .font(.system(size: 9))
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 12)
                    .padding(.bottom, 4)
                }

                HStack {
                    Spacer()
                    Text("\(manager.filteredProjects.count) project(s) found")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .padding(.horizontal, 12)
                .padding(.bottom, 4)

                Divider().padding(.horizontal, 8)

                if manager.filteredProjects.isEmpty {
                    HStack {
                        Spacer()
                        Text(manager.rootFolder.isEmpty
                             ? "Set a root folder to browse projects"
                             : manager.searchQuery.isEmpty
                                ? "No .wirecup projects found"
                                : "No matching projects")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                    .padding(.vertical, 12)
                } else {
                    VStack(spacing: 0) {
                        ForEach(manager.filteredProjects) { project in
                            ProjectRow(project: project, manager: manager)
                        }
                    }
                    .frame(maxHeight: 280)
                }

                Divider().padding(.horizontal, 8)

                // Status bar — always visible
                HStack(spacing: 6) {
                    Circle()
                        .fill(manager.isRunning ? Color.green : (manager.statusText.contains("not found") || manager.statusText.contains("Failed") ? Color.red : Color.orange))
                        .frame(width: 7, height: 7)
                    Text(manager.statusText)
                        .font(.system(size: 11, weight: .medium))
                        .lineLimit(1)
                    Spacer()
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)

                if manager.isRunning {
                    HStack(spacing: 8) {
                        Button("Open Preview") { manager.openPreview() }
                            .buttonStyle(.borderedProminent)
                            .controlSize(.small)
                        Button("Stop") { manager.stop() }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                    }
                    .padding(.horizontal, 12)
                    .padding(.bottom, 6)
                }

                Divider().padding(.horizontal, 8)

                if manager.showSettings {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Settings")
                            .font(.system(size: 12, weight: .semibold))

                        HStack {
                            Text("Port:").font(.system(size: 10))
                            TextField("8765", text: $manager.customPort)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(size: 10))
                        }

                        Button("Set Root Folder...") { manager.chooseRootFolder() }
                            .font(.system(size: 11))
                        Button("Locate Wirecup Binary...") { manager.chooseWirecupBinary() }
                            .font(.system(size: 11))
                        Button("Close Settings") { manager.showSettings = false }
                            .font(.system(size: 11))
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                } else {
                    HStack(spacing: 4) {
                        Button("Settings") { manager.showSettings = true }
                            .font(.system(size: 12))
                        Spacer()
                        Button("Refresh") { manager.scanProjects() }
                            .font(.system(size: 12))
                    }
                }

                Divider().padding(.horizontal, 8)

                Button("Quit WirecupBar") { manager.stop(); NSApp.terminate(nil) }
                    .font(.system(size: 12))
                    .keyboardShortcut("q")
            }
            .padding(.bottom, 8)
            .frame(minWidth: 260)
            .onAppear {
                manager.scanProjects()
            }
        } label: {
            if manager.isRunning {
                HStack(spacing: 3) {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 6, height: 6)
                    Text(manager.currentProjectName)
                        .font(.system(size: 11))
                }
            } else {
                Image(systemName: "antenna.radiowaves.left.and.right.slash")
            }
        }
        .menuBarExtraStyle(.window)
    }
}

struct ProjectRow: View {
    let project: ProjectItem
    @ObservedObject var manager: WirecupManager

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "doc.richtext")
                .font(.system(size: 12))
                .foregroundColor(.accentColor)
                .frame(width: 16)

            Text(project.name)
                .font(.system(size: 12))
                .lineLimit(1)

            Spacer()

            if project.path == manager.projectPath && manager.isRunning {
                Button(action: { manager.openPreview() }) {
                    HStack(spacing: 2) {
                        Image(systemName: "safari")
                            .font(.system(size: 10))
                        Text("Open")
                            .font(.system(size: 11))
                    }
                }
                .buttonStyle(.borderless)
                .foregroundColor(.green)
                .keyboardShortcut("o")
            } else {
                Button(action: { manager.start(project: project) }) {
                    HStack(spacing: 2) {
                        Image(systemName: "play.fill")
                            .font(.system(size: 10))
                        Text("Start")
                            .font(.system(size: 11))
                    }
                }
                .buttonStyle(.borderless)
                .foregroundColor(.accentColor)
                .disabled(manager.isRunning)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
    }
}
