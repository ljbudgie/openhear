import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var wristband: WristbandBluetooth

    private let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .medium
        formatter.dateStyle = .none
        return formatter
    }()

    var body: some View {
        NavigationStack {
            Form {
                strengthSection
                sharpnessSection
                wristbandSection
                packetLogSection
                Section {
                    Text("Environmental sound awareness only. OpenHear Haptics is not a hearing aid or a medical device. This version plays and teaches the patterns. It does not listen or recognise sounds.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("About")
                }
            }
            .navigationTitle("Settings")
        }
    }

    // MARK: Strength

    private var strengthSection: some View {
        Section {
            VStack(alignment: .leading) {
                Text("Strength: \(model.intensity) of 255")
                Slider(
                    value: Binding(
                        get: { Double(model.intensity) },
                        set: { model.intensity = WristbandIntensity.clamped(Int($0.rounded())) }
                    ),
                    in: 0...255,
                    step: 1
                )
                .accessibilityLabel("Vibration strength")
                .accessibilityValue("\(model.intensity) of 255")
            }
            Button("Feel it with Knock") {
                if let knock = PatternLibrary.pattern(id: 7) { model.play(knock) }
            }
            .accessibilityHint("Plays the Knock pattern at this strength.")
            Button("Back to 200") { model.intensity = WristbandIntensity.defaultValue }
                .disabled(model.intensity == WristbandIntensity.defaultValue)
                .accessibilityLabel("Reset strength to 200")
        } header: {
            Text("Strength")
        } footer: {
            Text("The same 0 to 255 scale as the wristband. 200 is the default.")
        }
    }

    // MARK: Sharpness

    private var sharpnessSection: some View {
        Section {
            sharpnessSlider("Left motor only", value: \.leftOnly, test: 5)
            sharpnessSlider("Right motor only", value: \.rightOnly, test: 4)
            sharpnessSlider("Both motors", value: \.both, test: 2)
            Button("Restore 0.2, 0.9 and 0.5") { model.restoreDefaultTuning() }
                .disabled(model.tuning == .defaults)
                .accessibilityLabel("Restore default sharpness values")
        } header: {
            Text("Left and right feel")
        } footer: {
            Text("An iPhone has one vibration motor, so left and right are shown as different textures: soft for left, crisp for right. This is a design choice to test, not part of the wristband firmware.")
        }
    }

    private func sharpnessSlider(_ title: String, value: WritableKeyPath<HapticTuning, Float>, test patternId: Int) -> some View {
        VStack(alignment: .leading) {
            HStack {
                Text(title)
                Spacer()
                Text(String(format: "%.2f", model.tuning[keyPath: value]))
                    .monospacedDigit()
                    .foregroundStyle(.secondary)
            }
            .accessibilityHidden(true)
            HStack {
                Slider(
                    value: Binding(
                        get: { Double(model.tuning[keyPath: value]) },
                        set: { model.tuning[keyPath: value] = Float(($0 * 100).rounded() / 100) }
                    ),
                    in: 0...1,
                    step: 0.05
                )
                .accessibilityLabel("\(title) sharpness")
                .accessibilityValue(String(format: "%.2f", model.tuning[keyPath: value]))
                Button {
                    if let pattern = PatternLibrary.pattern(id: patternId) { model.play(pattern) }
                } label: {
                    Image(systemName: "play.circle")
                }
                .buttonStyle(.borderless)
                .accessibilityLabel("Feel \(title.lowercased())")
            }
        }
    }

    // MARK: Wristband

    private var wristbandSection: some View {
        Section {
            Text(wristband.status.text)
                .accessibilityLabel("Wristband status: \(wristband.status.text)")
            if wristband.isBusy {
                Button("Disconnect", role: .destructive) { wristband.disconnect() }
                    .accessibilityHint("Stops using Bluetooth.")
            } else {
                Button("Connect") { wristband.connect() }
                    .accessibilityHint("Starts Bluetooth and looks for an OpenHear or Bangle.js wristband.")
            }
            Toggle("Play on wristband too", isOn: $model.playOnWristband)
                .accessibilityHint("When on, each pattern is also sent to the connected wristband.")
            Stepper(value: $model.rampMs, in: 0...WristbandPacket.maxRampMs, step: 10) {
                Text("Onset ramp: \(model.rampMs) ms")
            }
            .accessibilityLabel("Onset ramp")
            .accessibilityValue("\(model.rampMs) milliseconds")
            Button("Send onset ramp to wristband") { model.sendRamp() }
                .disabled(!wristband.isConnected)
                .accessibilityHint("Sends the ramp setting packet to the connected wristband.")
        } header: {
            Text("Wristband")
        } footer: {
            Text("Bluetooth is not used until you tap Connect. Phone vibrations work without it. Packets are 3 bytes: sound class, strength, pattern. The onset ramp packet is 255, ramp divided by 2, 1.")
        }
    }

    // MARK: Packet log

    private var packetLogSection: some View {
        Section {
            if wristband.log.entries.isEmpty {
                Text("No packets sent yet.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(wristband.log.entries) { entry in
                    HStack {
                        Text(entry.hex)
                            .font(.system(.body, design: .monospaced))
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text(entry.label).font(.footnote)
                            Text(timeFormatter.string(from: entry.date))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel("\(entry.label), bytes \(entry.hex), sent at \(timeFormatter.string(from: entry.date))")
                }
                Button("Clear log") { wristband.clearLog() }
            }
        } header: {
            Text("Last 20 packets sent")
        }
    }
}
