import Foundation

// Pure description of what the phone plays for a pattern. HapticPlayer turns
// these into CHHapticEvents. Kept free of Core Haptics so it can be tested.

/// How left and right are shown on an iPhone, which has one motor.
///
/// These are a design choice to test, not part of the wristband firmware.
/// Tune the three defaults here, or live in the app's Settings screen.
struct HapticTuning: Equatable, Codable {
    /// Left motor only: soft and dull.
    static let leftOnlySharpness: Float = 0.2
    /// Right motor only: crisp.
    static let rightOnlySharpness: Float = 0.9
    /// Both motors together.
    static let bothSharpness: Float = 0.5

    var leftOnly: Float = HapticTuning.leftOnlySharpness
    var rightOnly: Float = HapticTuning.rightOnlySharpness
    var both: Float = HapticTuning.bothSharpness

    static let defaults = HapticTuning()

    func sharpness(for motors: Motors) -> Float {
        switch motors {
        case .left: return leftOnly
        case .right: return rightOnly
        case .both: return both
        }
    }
}

/// Wristband drive strength, 0 to 255, as in the 3-byte packet.
enum WristbandIntensity {
    static let range = 0...255
    static let defaultValue = 200

    static func clamped(_ value: Int) -> Int {
        min(range.upperBound, max(range.lowerBound, value))
    }

    /// Core Haptics intensity, 0.0 to 1.0: value / 255.
    static func hapticIntensity(_ value: Int) -> Float {
        Float(clamped(value)) / 255
    }
}

/// One continuous haptic event. Times are in seconds, as Core Haptics expects.
struct PlannedHapticEvent: Equatable {
    let relativeTime: TimeInterval
    let duration: TimeInterval
    let intensity: Float
    let sharpness: Float
    let motors: Motors
}

enum HapticPlan {
    /// Each "on" step becomes one continuous event. Pauses are gaps in relativeTime.
    static func events(for pattern: SoundPattern, intensity: Int, tuning: HapticTuning) -> [PlannedHapticEvent] {
        let level = WristbandIntensity.hapticIntensity(intensity)
        var events: [PlannedHapticEvent] = []
        var clockMs = 0
        for step in pattern.steps {
            if let motors = step.motors {
                events.append(PlannedHapticEvent(
                    relativeTime: TimeInterval(clockMs) / 1000,
                    duration: TimeInterval(step.durationMs) / 1000,
                    intensity: level,
                    sharpness: tuning.sharpness(for: motors),
                    motors: motors
                ))
            }
            clockMs += step.durationMs
        }
        return events
    }
}
