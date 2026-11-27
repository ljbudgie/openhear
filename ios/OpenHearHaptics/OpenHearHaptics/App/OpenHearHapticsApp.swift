import SwiftUI

@main
struct OpenHearHapticsApp: App {
    @StateObject private var model = AppModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .environmentObject(model.haptics)
                .environmentObject(model.wristband)
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                model.haptics.appBecameActive()
            }
        }
    }
}
