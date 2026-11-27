import XCTest
@testable import OpenHearHaptics

final class PacketTests: XCTestCase {
    func testPatternPacketIsClassIntensityPattern() throws {
        for pattern in PatternLibrary.all {
            XCTAssertEqual(
                WristbandPacket.pattern(pattern, intensity: 200),
                [UInt8(pattern.id), 200, UInt8(pattern.id)]
            )
        }
    }

    func testIntensityIsClampedToAByte() throws {
        let doorbell = try XCTUnwrap(PatternLibrary.pattern(id: 2))
        XCTAssertEqual(WristbandPacket.pattern(doorbell, intensity: 300), [2, 255, 2])
        XCTAssertEqual(WristbandPacket.pattern(doorbell, intensity: -5), [2, 0, 2])
    }

    func testRampPacketMatchesPythonReference() {
        // stream/haptic_packet.py ramp_config_packet
        XCTAssertEqual(WristbandPacket.ramp(ms: 0), [255, 0, 1])
        XCTAssertEqual(WristbandPacket.ramp(ms: 40), [255, 20, 1])
        XCTAssertEqual(WristbandPacket.ramp(ms: 510), [255, 255, 1])
        XCTAssertEqual(WristbandPacket.ramp(ms: 1000), [255, 255, 1])
        XCTAssertEqual(WristbandPacket.ramp(ms: -10), [255, 0, 1])
        XCTAssertEqual(WristbandPacket.ramp(ms: 5), [255, 2, 1]) // Python round(2.5) == 2
        XCTAssertEqual(WristbandPacket.ramp(ms: 7), [255, 4, 1]) // Python round(3.5) == 4
    }

    func testHex() {
        XCTAssertEqual(WristbandPacket.hex([1, 200, 1]), "01 C8 01")
        XCTAssertEqual(WristbandPacket.hex([255, 20, 1]), "FF 14 01")
    }

    func testLogKeepsLastTwentyNewestFirst() {
        var log = PacketLog()
        for i in 0..<25 {
            log.append([UInt8(i), 0, 0], label: "packet \(i)")
        }
        XCTAssertEqual(log.entries.count, 20)
        XCTAssertEqual(log.entries.first?.label, "packet 24")
        XCTAssertEqual(log.entries.last?.label, "packet 5")
        log.clear()
        XCTAssertTrue(log.entries.isEmpty)
    }
}

final class PracticeStatsTests: XCTestCase {
    func testRecordsTriesCorrectAndMixUps() {
        var stats = PracticeStats()
        XCTAssertTrue(stats.recordAnswer(actual: 7, guess: 7))
        XCTAssertFalse(stats.recordAnswer(actual: 7, guess: 2))
        XCTAssertFalse(stats.recordAnswer(actual: 7, guess: 8))
        XCTAssertFalse(stats.recordAnswer(actual: 7, guess: 8))
        let knock = stats.record(for: 7)
        XCTAssertEqual(knock.tries, 4)
        XCTAssertEqual(knock.correct, 1)
        XCTAssertEqual(knock.mostCommonMixUp, 8)
        XCTAssertEqual(stats.totalTries, 4)
        XCTAssertEqual(stats.totalCorrect, 1)
    }

    func testTieGoesToLowerId() {
        var stats = PracticeStats()
        stats.recordAnswer(actual: 1, guess: 6)
        stats.recordAnswer(actual: 1, guess: 3)
        XCTAssertEqual(stats.record(for: 1).mostCommonMixUp, 3)
    }

    func testNoMixUpWhenAlwaysRight() {
        var stats = PracticeStats()
        stats.recordAnswer(actual: 4, guess: 4)
        XCTAssertNil(stats.record(for: 4).mostCommonMixUp)
    }

    func testRoundTripAndReset() throws {
        var stats = PracticeStats()
        stats.recordAnswer(actual: 9, guess: 3)
        let restored = try PracticeStats.decoded(from: stats.encoded())
        XCTAssertEqual(restored, stats)
        stats.reset()
        XCTAssertEqual(stats.totalTries, 0)
    }
}
