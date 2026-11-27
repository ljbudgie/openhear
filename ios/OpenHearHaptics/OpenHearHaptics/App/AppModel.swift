import Foundation
import SwiftUI

/// App-wide state: settings, practice results, and the two outputs
/// (phone haptics always, wristband only when switched on and connected).
@MainActor
final class AppModel: ObservableObject {
    let haptics: HapticPlayer
    let wristband: WristbandBluetooth

    @Published var intensity: Int {
        didSet { defaults.set(intensity, forKey: Keys.intensity) }
    }
    @Published var tuning: HapticTuning {
        didSet { save(tuning, forKey: Keys.tuning) }
    }
    /// Off at every launch, by design.
    @Published var playOnWristband = false
    @Published var rampMs: Int {
        didSet { defaults.set(rampMs, forKey: Keys.rampMs) }
    }
    @Published private(set) var practice: PracticeStats

    private let defaults: UserDefaults

    private enum Keys {
        static let intensity = "intensity"
        static let tuning = "hapticTuning"
        static let rampMs = "rampMs"
        static let practice = "practiceStats"
    }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        haptics = HapticPlayer()
        wristband = WristbandBluetooth()
        if defaults.object(forKey: Keys.intensity) != nil {
            intensity = WristbandIntensity.clamped(defaults.integer(forKey: Keys.intensity))
        } else {
            intensity = WristbandIntensity.defaultValue
        }
        tuning = (defaults.data(forKey: Keys.tuning)).flatMap { try? JSONDecoder().decode(HapticTuning.self, from: $0) }
            ?? .defaults
        rampMs = min(WristbandPacket.maxRampMs, max(0, defaults.integer(forKey: Keys.rampMs)))
        practice = (defaults.data(forKey: Keys.practice)).flatMap { try? PracticeStats.decoded(from: $0) }
            ?? PracticeStats()
    }

    /// Plays a pattern on the phone, and on the wristband too if that is switched on.
    func play(_ pattern: SoundPattern) {
        haptics.play(pattern, intensity: intensity, tuning: tuning)
        if playOnWristband {
            wristband.send(WristbandPacket.pattern(pattern, intensity: intensity), label: pattern.name)
        }
    }

    func sendRamp() {
        wristband.send(WristbandPacket.ramp(ms: rampMs), label: "Onset ramp \(rampMs) ms")
    }

    @discardableResult
    func recordAnswer(actual: SoundPattern, guess: SoundPattern) -> Bool {
        let isRight = practice.recordAnswer(actual: actual.id, guess: guess.id)
        savePractice()
        return isRight
    }

    func resetPractice() {
        practice.reset()
        savePractice()
    }

    func restoreDefaultTuning() {
        tuning = .defaults
    }

    private func savePractice() {
        if let data = try? practice.encoded() {
            defaults.set(data, forKey: Keys.practice)
        }
    }

    private func save<T: Encodable>(_ value: T, forKey key: String) {
        if let data = try? JSONEncoder().encode(value) {
            defaults.set(data, forKey: key)
        }
    }
}
