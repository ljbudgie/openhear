import Foundation

// Practice ("Name the sound") results. Stored on this iPhone only, in
// UserDefaults, by AppModel.

struct PatternRecord: Codable, Equatable {
    var tries = 0
    var correct = 0
    /// Guessed pattern id -> how many times it was guessed by mistake.
    var mixUps: [Int: Int] = [:]

    /// The wrong answer given most often. Ties go to the lower pattern id.
    var mostCommonMixUp: Int? {
        mixUps
            .filter { $0.value > 0 }
            .sorted { lhs, rhs in lhs.value != rhs.value ? lhs.value > rhs.value : lhs.key < rhs.key }
            .first?
            .key
    }
}

struct PracticeStats: Codable, Equatable {
    /// Pattern id -> record.
    private(set) var records: [Int: PatternRecord] = [:]

    func record(for patternId: Int) -> PatternRecord {
        records[patternId] ?? PatternRecord()
    }

    /// Returns true if the guess was right.
    @discardableResult
    mutating func recordAnswer(actual: Int, guess: Int) -> Bool {
        var record = record(for: actual)
        record.tries += 1
        let isRight = actual == guess
        if isRight {
            record.correct += 1
        } else {
            record.mixUps[guess, default: 0] += 1
        }
        records[actual] = record
        return isRight
    }

    mutating func reset() {
        records.removeAll()
    }

    var totalTries: Int { records.values.reduce(0) { $0 + $1.tries } }
    var totalCorrect: Int { records.values.reduce(0) { $0 + $1.correct } }

    func encoded() throws -> Data {
        try JSONEncoder().encode(self)
    }

    static func decoded(from data: Data) throws -> PracticeStats {
        try JSONDecoder().decode(PracticeStats.self, from: data)
    }
}
