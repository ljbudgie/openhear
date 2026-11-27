import Foundation

// The nine OpenHear wristband vibration patterns.
//
// Copied from wristband/openhear_firmware.py (the canonical micro:bit v1.0.0
// firmware). Each step is (left motor, right motor, milliseconds). A step with
// both motors off is a pause. Sound class id and pattern id are the same
// number, 1 to 9, as in stream/haptic_mapper.py.
//
// If the firmware changes, change this table and the tests in
// OpenHearHapticsTests/PatternsTests.swift together, then run
// Scripts/check_patterns.py.

/// Which motors a step drives.
enum Motors: String, Codable, CaseIterable {
    case left
    case right
    case both
}

/// One step of a pattern.
struct PatternStep: Hashable, Codable {
    let left: Bool
    let right: Bool
    let durationMs: Int

    /// Mirrors the firmware notation: PatternStep(1, 1, 200) is both motors for 200 ms.
    init(_ left: Int, _ right: Int, _ durationMs: Int) {
        self.left = left != 0
        self.right = right != 0
        self.durationMs = durationMs
    }

    var isPause: Bool { !left && !right }

    /// nil for a pause.
    var motors: Motors? {
        switch (left, right) {
        case (true, true): return .both
        case (true, false): return .left
        case (false, true): return .right
        case (false, false): return nil
        }
    }
}

/// A stretch of time where one motor lane is on, used to draw the timing strip.
struct LaneSegment: Hashable {
    let startMs: Int
    let durationMs: Int
}

/// One wristband sound pattern.
struct SoundPattern: Identifiable, Hashable {
    /// Sound class id and pattern id (they are the same number, 1 to 9).
    let id: Int
    /// Firmware and classifier key, for example "baby_cry".
    let key: String
    /// Name shown in the app.
    let name: String
    /// One-line description of how it feels.
    let summary: String
    let steps: [PatternStep]

    var soundClassId: Int { id }
    var patternId: Int { id }

    var totalMs: Int { steps.reduce(0) { $0 + $1.durationMs } }

    /// The times one lane (left or right motor) is on.
    func laneSegments(left: Bool) -> [LaneSegment] {
        var segments: [LaneSegment] = []
        var clock = 0
        for step in steps {
            let on = left ? step.left : step.right
            if on {
                segments.append(LaneSegment(startMs: clock, durationMs: step.durationMs))
            }
            clock += step.durationMs
        }
        return segments
    }

    /// Text for VoiceOver describing the timing strip.
    var accessibleTiming: String {
        "\(summary) Lasts \(totalMs) milliseconds."
    }
}

private func repeated(_ times: Int, _ block: [PatternStep]) -> [PatternStep] {
    (0..<times).flatMap { _ in block }
}

enum PatternLibrary {
    static let all: [SoundPattern] = [
        SoundPattern(
            id: 1, key: "voice", name: "Someone speaking",
            summary: "Both sides, three steady pulses.",
            steps: repeated(3, [PatternStep(1, 1, 200), PatternStep(0, 0, 100)])
        ),
        SoundPattern(
            id: 2, key: "doorbell", name: "Doorbell",
            summary: "Both sides, two quick taps.",
            steps: repeated(2, [PatternStep(1, 1, 50), PatternStep(0, 0, 50)])
        ),
        SoundPattern(
            id: 3, key: "alarm", name: "Alarm",
            summary: "Fast left, right, left, right, eight beats.",
            steps: (0..<8).flatMap { step in
                [step % 2 == 0 ? PatternStep(1, 0, 30) : PatternStep(0, 1, 30), PatternStep(0, 0, 30)]
            }
        ),
        SoundPattern(
            id: 4, key: "dog", name: "Dog barking",
            summary: "Right side, one short pulse.",
            steps: [PatternStep(0, 1, 150)]
        ),
        SoundPattern(
            id: 5, key: "traffic", name: "Vehicle warning",
            summary: "Left side, one long pulse.",
            steps: [PatternStep(1, 0, 300)]
        ),
        SoundPattern(
            id: 6, key: "media", name: "Music or TV",
            summary: "Both sides, two slow long pulses.",
            steps: repeated(2, [PatternStep(1, 1, 500), PatternStep(0, 0, 500)])
        ),
        SoundPattern(
            id: 7, key: "knock", name: "Knock",
            summary: "Both sides, a longer tap then a short one.",
            steps: [PatternStep(1, 1, 80), PatternStep(0, 0, 40), PatternStep(1, 1, 40)]
        ),
        SoundPattern(
            id: 8, key: "baby_cry", name: "Baby crying",
            summary: "Both sides, four quick pulses.",
            steps: repeated(4, [PatternStep(1, 1, 60), PatternStep(0, 0, 40)])
        ),
        SoundPattern(
            id: 9, key: "phone", name: "Phone ringing",
            summary: "Left then right, three times.",
            steps: repeated(3, [
                PatternStep(1, 0, 100), PatternStep(0, 0, 80),
                PatternStep(0, 1, 100), PatternStep(0, 0, 80),
            ])
        ),
    ]

    static func pattern(id: Int) -> SoundPattern? {
        all.first { $0.id == id }
    }
}
