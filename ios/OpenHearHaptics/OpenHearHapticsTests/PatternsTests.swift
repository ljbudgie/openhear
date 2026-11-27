import XCTest
@testable import OpenHearHaptics

/// Checks Patterns.swift against wristband/openhear_firmware.py.
final class PatternsTests: XCTestCase {
    private func s(_ left: Int, _ right: Int, _ ms: Int) -> PatternStep { PatternStep(left, right, ms) }

    func testThereAreNinePatternsWithIdsOneToNine() {
        XCTAssertEqual(PatternLibrary.all.map(\.id), Array(1...9))
        XCTAssertEqual(PatternLibrary.all.map(\.soundClassId), Array(1...9))
        XCTAssertEqual(PatternLibrary.all.map(\.patternId), Array(1...9))
    }

    func testKeysAndNames() {
        XCTAssertEqual(
            PatternLibrary.all.map(\.key),
            ["voice", "doorbell", "alarm", "dog", "traffic", "media", "knock", "baby_cry", "phone"]
        )
        XCTAssertEqual(
            PatternLibrary.all.map(\.name),
            ["Someone speaking", "Doorbell", "Alarm", "Dog barking", "Vehicle warning",
             "Music or TV", "Knock", "Baby crying", "Phone ringing"]
        )
    }

    func testTotals() {
        let expected: [Int: Int] = [
            1: 900, 2: 200, 3: 480, 4: 150, 5: 300, 6: 2000, 7: 160, 8: 400, 9: 1080,
        ]
        for pattern in PatternLibrary.all {
            XCTAssertEqual(pattern.totalMs, expected[pattern.id], "Total for \(pattern.key)")
        }
    }

    func testVoiceSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 1)?.steps, [
            s(1, 1, 200), s(0, 0, 100),
            s(1, 1, 200), s(0, 0, 100),
            s(1, 1, 200), s(0, 0, 100),
        ])
    }

    func testDoorbellSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 2)?.steps, [
            s(1, 1, 50), s(0, 0, 50),
            s(1, 1, 50), s(0, 0, 50),
        ])
    }

    func testAlarmSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 3)?.steps, [
            s(1, 0, 30), s(0, 0, 30), s(0, 1, 30), s(0, 0, 30),
            s(1, 0, 30), s(0, 0, 30), s(0, 1, 30), s(0, 0, 30),
            s(1, 0, 30), s(0, 0, 30), s(0, 1, 30), s(0, 0, 30),
            s(1, 0, 30), s(0, 0, 30), s(0, 1, 30), s(0, 0, 30),
        ])
    }

    func testDogSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 4)?.steps, [s(0, 1, 150)])
    }

    func testTrafficSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 5)?.steps, [s(1, 0, 300)])
    }

    func testMediaSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 6)?.steps, [
            s(1, 1, 500), s(0, 0, 500),
            s(1, 1, 500), s(0, 0, 500),
        ])
    }

    func testKnockSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 7)?.steps, [s(1, 1, 80), s(0, 0, 40), s(1, 1, 40)])
    }

    func testBabyCrySteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 8)?.steps, [
            s(1, 1, 60), s(0, 0, 40),
            s(1, 1, 60), s(0, 0, 40),
            s(1, 1, 60), s(0, 0, 40),
            s(1, 1, 60), s(0, 0, 40),
        ])
    }

    func testPhoneSteps() {
        XCTAssertEqual(PatternLibrary.pattern(id: 9)?.steps, [
            s(1, 0, 100), s(0, 0, 80), s(0, 1, 100), s(0, 0, 80),
            s(1, 0, 100), s(0, 0, 80), s(0, 1, 100), s(0, 0, 80),
            s(1, 0, 100), s(0, 0, 80), s(0, 1, 100), s(0, 0, 80),
        ])
    }

    func testLaneSegmentsForPhone() throws {
        let phone = try XCTUnwrap(PatternLibrary.pattern(id: 9))
        XCTAssertEqual(phone.laneSegments(left: true).map(\.startMs), [0, 360, 720])
        XCTAssertEqual(phone.laneSegments(left: false).map(\.startMs), [180, 540, 900])
        XCTAssertTrue(phone.laneSegments(left: true).allSatisfy { $0.durationMs == 100 })
    }
}

final class HapticPlanTests: XCTestCase {
    func testDefaultSharpnessConstants() {
        XCTAssertEqual(HapticTuning.leftOnlySharpness, 0.2)
        XCTAssertEqual(HapticTuning.rightOnlySharpness, 0.9)
        XCTAssertEqual(HapticTuning.bothSharpness, 0.5)
        XCTAssertEqual(WristbandIntensity.defaultValue, 200)
    }

    func testIntensityIsValueOver255() {
        XCTAssertEqual(WristbandIntensity.hapticIntensity(255), 1.0)
        XCTAssertEqual(WristbandIntensity.hapticIntensity(0), 0.0)
        XCTAssertEqual(WristbandIntensity.hapticIntensity(200), 200.0 / 255.0, accuracy: 0.0001)
        XCTAssertEqual(WristbandIntensity.hapticIntensity(400), 1.0)
    }

    func testVoiceEventsArePulsesWithGaps() throws {
        let voice = try XCTUnwrap(PatternLibrary.pattern(id: 1))
        let events = HapticPlan.events(for: voice, intensity: 200, tuning: .defaults)
        XCTAssertEqual(events.count, 3)
        assertTimes(events.map(\.relativeTime), [0.0, 0.3, 0.6], accuracy: 0.0001)
        XCTAssertTrue(events.allSatisfy { abs($0.duration - 0.2) < 0.0001 })
        XCTAssertTrue(events.allSatisfy { $0.sharpness == HapticTuning.bothSharpness })
    }

    func testLeftAndRightUseTheirSharpness() throws {
        let alarm = try XCTUnwrap(PatternLibrary.pattern(id: 3))
        let events = HapticPlan.events(for: alarm, intensity: 255, tuning: .defaults)
        XCTAssertEqual(events.count, 8)
        XCTAssertEqual(events.map(\.motors), [.left, .right, .left, .right, .left, .right, .left, .right])
        XCTAssertEqual(events[0].sharpness, HapticTuning.leftOnlySharpness)
        XCTAssertEqual(events[1].sharpness, HapticTuning.rightOnlySharpness)
        assertTimes(events.map(\.relativeTime), [0.0, 0.06, 0.12, 0.18, 0.24, 0.3, 0.36, 0.42], accuracy: 0.0001)
    }

    func testEveryPatternEndsWithinItsTotal() {
        for pattern in PatternLibrary.all {
            let events = HapticPlan.events(for: pattern, intensity: 200, tuning: .defaults)
            let onSteps = pattern.steps.filter { !$0.isPause }
            XCTAssertEqual(events.count, onSteps.count, pattern.key)
            let end = events.map { $0.relativeTime + $0.duration }.max() ?? 0
            XCTAssertLessThanOrEqual(end, Double(pattern.totalMs) / 1000 + 0.0001, pattern.key)
        }
    }
}

private func assertTimes(
    _ lhs: [Double], _ rhs: [Double], accuracy: Double,
    file: StaticString = #filePath, line: UInt = #line
) {
    XCTAssertEqual(lhs.count, rhs.count, file: file, line: line)
    for (a, b) in zip(lhs, rhs) {
        XCTAssertEqual(a, b, accuracy: accuracy, file: file, line: line)
    }
}
