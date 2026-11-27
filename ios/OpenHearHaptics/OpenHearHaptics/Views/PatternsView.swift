import SwiftUI

struct PatternsView: View {
    @EnvironmentObject private var haptics: HapticPlayer

    var body: some View {
        NavigationStack {
            List {
                if !haptics.supportsHaptics {
                    Section { NoHapticsNotice() }
                }
                if let problem = haptics.problem {
                    Section { HapticProblemNotice(message: problem) }
                }
                Section {
                    ForEach(PatternLibrary.all) { pattern in
                        PatternRow(pattern: pattern)
                    }
                } footer: {
                    Text("Tap a pattern to feel it. Environmental sound awareness only. OpenHear Haptics is not a hearing aid or a medical device.")
                }
            }
            .navigationTitle("Patterns")
        }
    }
}

private struct PatternRow: View {
    let pattern: SoundPattern

    @EnvironmentObject private var model: AppModel
    @State private var progress: Double = 0
    @State private var playToken = 0

    var body: some View {
        HStack(alignment: .center, spacing: 12) {
            VStack(alignment: .leading, spacing: 6) {
                Text(pattern.name)
                    .font(.headline)
                Text(pattern.summary)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                TimingStrip(pattern: pattern, progress: progress)
            }
            Spacer(minLength: 8)
            Button(action: play) {
                Image(systemName: "play.circle.fill")
                    .font(.largeTitle)
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("Play \(pattern.name)")
            .accessibilityHint("Plays this vibration on the iPhone.")
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        .onTapGesture(perform: play)
    }

    private func play() {
        model.play(pattern)
        playToken += 1
        let token = playToken
        let seconds = Double(pattern.totalMs) / 1000
        let instant: Transaction = {
            var transaction = Transaction()
            transaction.disablesAnimations = true
            return transaction
        }()
        withTransaction(instant) { progress = 0 }
        Task { @MainActor in
            // Let the reset to 0 draw before animating to 1.
            try? await Task.sleep(for: .milliseconds(16))
            guard token == playToken else { return }
            withAnimation(.linear(duration: seconds)) { progress = 1 }
            try? await Task.sleep(for: .seconds(seconds + 0.4))
            guard token == playToken else { return }
            withTransaction(instant) { progress = 0 }
        }
    }
}
