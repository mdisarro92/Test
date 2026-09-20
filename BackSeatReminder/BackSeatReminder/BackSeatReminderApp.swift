import SwiftUI

@main
struct BackSeatReminderApp: App {
    @StateObject private var monitor: DriveMonitor

    init() {
        let notifications = NotificationManager()
        notifications.configure()
        _monitor = StateObject(
            wrappedValue: DriveMonitor(notificationManager: notifications)
        )
    }

    var body: some Scene {
        WindowGroup {
            ContentView(monitor: monitor)
        }
    }
}
