import SwiftUI

/// "Name the sound": feel a random pattern with no visual hint, then pick its name.
struct PracticeView: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var haptics: HapticPlayer

    @State private var current: SoundPattern?
    @State private var guess: SoundPattern?
    @State private var confirmingReset = false

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
                    if let current {
                        Button {
                            model.play(current)
                        } label: {
                            Label("Feel it again", systemImage: "arrow.counterclockwise")
                        }
                        .accessibilityHint("Plays the same pattern again.")
                    }
                    Button(action: nextSound) {
                        Label(nextButtonTitle, systemImage: "play.circle")
                    }
                    .accessibilityHint("Plays a random pattern for you to name.")
                } header: {
                    Text("Name the sound")
                } footer: {
                    Text("Feel the pattern, then choose which sound it stands for.")
                }

                if let current {
                    Section {
                        if let guess {
                            resultView(actual: current, guess: guess)
                        }
                        ForEach(PatternLibrary.all) { option in
                            answerButton(option, actual: current)
                        }
                    } header: {
                        Text(guess == nil ? "Which sound was it?" : "Result")
                    }
                }

                resultsSection
            }
            .navigationTitle("Practice")
            .confirmationDialog(
                "Reset all practice results?",
                isPresented: $confirmingReset,
                titleVisibility: .visible
            ) {
                Button("Reset results", role: .destructive) { model.resetPractice() }
                Button("Cancel", role: .cancel) {}
            }
        }
    }

    private var nextButtonTitle: String {
        if current == nil { return "Feel a sound" }
        return guess == nil ? "Skip to a new sound" : "Next sound"
    }

    private func nextSound() {
        let choices = PatternLibrary.all.filter { $0.id != current?.id }
        guard let pick = choices.randomElement() ?? PatternLibrary.all.randomElement() else { return }
        current = pick
        guess = nil
        model.play(pick)
    }

    private func choose(_ option: SoundPattern, actual: SoundPattern) {
        guard guess == nil else { return }
        guess = option
        let isRight = model.recordAnswer(actual: actual, guess: option)
        AccessibilityNotification.Announcement(resultText(actual: actual, guess: option, isRight: isRight)).post()
    }

    private func resultText(actual: SoundPattern, guess: SoundPattern, isRight: Bool) -> String {
        isRight
            ? "Right. It was \(actual.name)."
            : "Not quite. It was \(actual.name). You chose \(guess.name)."
    }

    private func resultView(actual: SoundPattern, guess: SoundPattern) -> some View {
        let isRight = actual.id == guess.id
        return Label {
            Text(resultText(actual: actual, guess: guess, isRight: isRight))
                .font(.headline)
        } icon: {
            Image(systemName: isRight ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundStyle(isRight ? .green : .red)
        }
        .accessibilityElement(children: .combine)
    }

    private func answerButton(_ option: SoundPattern, actual: SoundPattern) -> some View {
        Button {
            choose(option, actual: actual)
        } label: {
            HStack {
                Text(option.name)
                    .foregroundStyle(.primary)
                Spacer()
                if guess != nil {
                    if option.id == actual.id {
                        Image(systemName: "checkmark").foregroundStyle(.green)
                    } else if option.id == guess?.id {
                        Image(systemName: "xmark").foregroundStyle(.red)
                    }
                }
            }
        }
        .disabled(guess != nil)
        .accessibilityLabel(answerLabel(option, actual: actual))
        .accessibilityHint(guess == nil ? "Choose this as your answer." : "")
    }

    private func answerLabel(_ option: SoundPattern, actual: SoundPattern) -> String {
        guard guess != nil else { return option.name }
        if option.id == actual.id { return "\(option.name), correct answer" }
        if option.id == guess?.id { return "\(option.name), your answer" }
        return option.name
    }

    private var resultsSection: some View {
        Section {
            ForEach(PatternLibrary.all) { pattern in
                let record = model.practice.record(for: pattern.id)
                VStack(alignment: .leading, spacing: 2) {
                    Text(pattern.name).font(.body)
                    Text(recordText(record))
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                .accessibilityElement(children: .combine)
            }
            Button("Reset results", role: .destructive) { confirmingReset = true }
                .disabled(model.practice.totalTries == 0)
                .accessibilityHint("Clears all practice results on this iPhone.")
        } header: {
            Text("Your results: \(model.practice.totalCorrect) right out of \(model.practice.totalTries)")
        } footer: {
            Text("Results are kept on this iPhone only.")
        }
    }

    private func recordText(_ record: PatternRecord) -> String {
        guard record.tries > 0 else { return "Not tried yet." }
        var text = "\(record.correct) right out of \(record.tries)."
        if let mixUp = record.mostCommonMixUp, let other = PatternLibrary.pattern(id: mixUp) {
            text += " Most often mixed up with \(other.name)."
        }
        return text
    }
}
