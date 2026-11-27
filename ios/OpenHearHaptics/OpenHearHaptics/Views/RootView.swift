import SwiftUI

struct RootView: View {
    var body: some View {
        TabView {
            PatternsView()
                .tabItem { Label("Patterns", systemImage: "waveform.path") }
            PracticeView()
                .tabItem { Label("Practice", systemImage: "questionmark.circle") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gearshape") }
        }
    }
}

/// Shown when the phone cannot play custom vibrations (including the Simulator).
struct NoHapticsNotice: View {
    var body: some View {
        Label {
            Text("This device cannot play custom vibrations, so you will not feel the patterns here. The timing strips still show what each pattern does, and the wristband can still be used.")
        } icon: {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)
        }
        .font(.callout)
        .accessibilityElement(children: .combine)
    }
}

/// Shown when the haptic engine reported a problem.
struct HapticProblemNotice: View {
    let message: String

    var body: some View {
        Label(message, systemImage: "exclamationmark.circle")
            .font(.callout)
            .foregroundStyle(.red)
            .accessibilityElement(children: .combine)
    }
}
