import Foundation

// The OpenHear wristband packet format, matching stream/haptic_packet.py and
// wristband/openhear_firmware.py:
//
//   [sound class id, intensity 0-255, pattern id]
//
// Onset ramp control packet: [255, ramp_ms / 2, 1].

enum WristbandPacket {
    static let controlSoundClassId: UInt8 = 255
    static let setRampPatternId: UInt8 = 1
    static let rampUnitMs = 2
    /// The largest ramp one byte can carry: 255 x 2 ms.
    static let maxRampMs = 255 * 2

    static func pattern(_ pattern: SoundPattern, intensity: Int) -> [UInt8] {
        [
            UInt8(clamping: pattern.soundClassId),
            UInt8(WristbandIntensity.clamped(intensity)),
            UInt8(clamping: pattern.patternId),
        ]
    }

    /// Same rounding as ramp_config_packet in stream/haptic_packet.py.
    static func ramp(ms: Int) -> [UInt8] {
        let units = (Double(ms) / Double(rampUnitMs)).rounded(.toNearestOrEven)
        let encoded = min(255, max(0, Int(units)))
        return [controlSoundClassId, UInt8(encoded), setRampPatternId]
    }

    static func hex(_ bytes: [UInt8]) -> String {
        bytes.map { byte in
            let digits = String(byte, radix: 16, uppercase: true)
            return digits.count == 1 ? "0" + digits : digits
        }.joined(separator: " ")
    }
}

/// The most recent packets sent to the wristband, newest first.
struct PacketLog: Equatable {
    struct Entry: Identifiable, Equatable {
        let id: UUID
        let date: Date
        let bytes: [UInt8]
        let label: String

        var hex: String { WristbandPacket.hex(bytes) }
    }

    static let capacity = 20

    private(set) var entries: [Entry] = []

    mutating func append(_ bytes: [UInt8], label: String, date: Date = Date()) {
        entries.insert(Entry(id: UUID(), date: date, bytes: bytes, label: label), at: 0)
        if entries.count > Self.capacity {
            entries.removeLast(entries.count - Self.capacity)
        }
    }

    mutating func clear() {
        entries.removeAll()
    }
}
