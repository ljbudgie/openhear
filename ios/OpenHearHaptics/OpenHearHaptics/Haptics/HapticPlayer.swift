import CoreHaptics
import Foundation

/// Plays OpenHear patterns on the iPhone's Taptic Engine with Core Haptics.
///
/// One CHHapticPattern is built per sound from HapticPlan, and played with a
/// pattern player. If the engine stops or resets, it is restarted, and a
/// pattern that was cut off part way is played again from the start.
@MainActor
final class HapticPlayer: ObservableObject {
    /// False on devices without custom haptics (older iPhones, the Simulator).
    @Published private(set) var supportsHaptics: Bool
    /// A plain-English problem to show, or nil when all is well.
    @Published private(set) var problem: String?

    private var engine: CHHapticEngine?
    private var player: CHHapticPatternPlayer?
    private var current: (pattern: SoundPattern, intensity: Int, tuning: HapticTuning, endsAt: Date)?

    init() {
        supportsHaptics = CHHapticEngine.capabilitiesForHardware().supportsHaptics
        if supportsHaptics {
            do {
                try prepareEngine().start()
            } catch {
                problem = "The vibration engine did not start: \(error.localizedDescription)"
            }
        }
    }

    func play(_ pattern: SoundPattern, intensity: Int, tuning: HapticTuning) {
        guard supportsHaptics else { return }
        current = (pattern, intensity, tuning, Date().addingTimeInterval(Double(pattern.totalMs) / 1000))
        start(pattern, intensity: intensity, tuning: tuning)
    }

    func stop() {
        try? player?.stop(atTime: CHHapticTimeImmediate)
        player = nil
        current = nil
    }

    /// Call when the app comes back to the foreground.
    func appBecameActive() {
        guard supportsHaptics else { return }
        try? engine?.start()
    }

    // MARK: - Private

    private func start(_ pattern: SoundPattern, intensity: Int, tuning: HapticTuning) {
        do {
            let engine = try prepareEngine()
            try engine.start()
            let events = HapticPlan.events(for: pattern, intensity: intensity, tuning: tuning).map { planned in
                CHHapticEvent(
                    eventType: .hapticContinuous,
                    parameters: [
                        CHHapticEventParameter(parameterID: .hapticIntensity, value: planned.intensity),
                        CHHapticEventParameter(parameterID: .hapticSharpness, value: planned.sharpness),
                    ],
                    relativeTime: planned.relativeTime,
                    duration: planned.duration
                )
            }
            let hapticPattern = try CHHapticPattern(events: events, parameters: [])
            try? player?.stop(atTime: CHHapticTimeImmediate)
            let newPlayer = try engine.makePlayer(with: hapticPattern)
            try newPlayer.start(atTime: CHHapticTimeImmediate)
            player = newPlayer
            problem = nil
        } catch {
            problem = "The vibration could not play: \(error.localizedDescription)"
        }
    }

    private func prepareEngine() throws -> CHHapticEngine {
        if let engine { return engine }
        let newEngine = try CHHapticEngine()
        newEngine.playsHapticsOnly = true
        newEngine.isAutoShutdownEnabled = true
        // Core Haptics calls these on its own queue, so hop to the main actor.
        newEngine.stoppedHandler = { @Sendable [weak self] reason in
            guard let self else { return }
            Task { @MainActor in self.engineStopped(reason) }
        }
        newEngine.resetHandler = { @Sendable [weak self] in
            guard let self else { return }
            Task { @MainActor in self.engineReset() }
        }
        engine = newEngine
        return newEngine
    }

    private func engineStopped(_ reason: CHHapticEngine.StoppedReason) {
        player = nil
        switch reason {
        case .idleTimeout, .applicationSuspended:
            // Normal. The engine is started again on the next play or when
            // the app comes back to the foreground.
            return
        default:
            resumeOrRestart()
        }
    }

    private func engineReset() {
        // After a reset every player is invalid. Restart and carry on.
        player = nil
        resumeOrRestart()
    }

    private func resumeOrRestart() {
        if let current, Date() < current.endsAt {
            play(current.pattern, intensity: current.intensity, tuning: current.tuning)
        } else {
            do {
                try engine?.start()
            } catch {
                problem = "The vibration engine stopped and did not restart: \(error.localizedDescription)"
            }
        }
    }
}
