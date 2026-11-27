import SwiftUI

/// Two lanes, left and right motor, drawn to scale from the pattern table.
/// `progress` (0 to 1) lights the lanes up as the pattern plays.
struct TimingStrip: View {
    let pattern: SoundPattern
    var progress: Double

    @ScaledMetric(relativeTo: .caption) private var laneHeight: CGFloat = 10

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            lane(title: "L", left: true, color: .blue)
            lane(title: "R", left: false, color: .orange)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Timing for \(pattern.name)")
        .accessibilityValue(pattern.accessibleTiming)
    }

    private func lane(title: String, left: Bool, color: Color) -> some View {
        HStack(spacing: 6) {
            Text(title)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(minWidth: 14, alignment: .leading)
            TimingLane(
                segments: pattern.laneSegments(left: left),
                totalMs: pattern.totalMs,
                progress: progress,
                color: color
            )
            .frame(height: laneHeight)
        }
    }
}

private struct TimingLane: View {
    let segments: [LaneSegment]
    let totalMs: Int
    let progress: Double
    let color: Color

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            ZStack(alignment: .leading) {
                Capsule().fill(Color.secondary.opacity(0.15))
                blocks(width: width).foregroundStyle(color.opacity(0.3))
                blocks(width: width)
                    .foregroundStyle(color)
                    .mask(alignment: .leading) {
                        Rectangle().frame(width: max(0, width * progress))
                    }
            }
        }
    }

    private func blocks(width: CGFloat) -> some View {
        let scale = totalMs > 0 ? width / CGFloat(totalMs) : 0
        return ZStack(alignment: .leading) {
            ForEach(segments, id: \.self) { segment in
                RoundedRectangle(cornerRadius: 2)
                    .frame(width: max(1, CGFloat(segment.durationMs) * scale))
                    .offset(x: CGFloat(segment.startMs) * scale)
            }
        }
        .frame(width: width, alignment: .leading)
    }
}
