import Foundation
import UserNotifications

final class NotificationManager: NSObject, UNUserNotificationCenterDelegate {
    static let categoryIdentifier = "BACK_SEAT_REMINDER"
    static let checkedActionIdentifier = "BACK_SEAT_CHECKED"
    static let remindAgainActionIdentifier = "BACK_SEAT_REMIND_AGAIN"

    private let center = UNUserNotificationCenter.current()

    func configure() {
        let checked = UNNotificationAction(
            identifier: Self.checkedActionIdentifier,
            title: "Checked",
            options: []
        )

        let remindAgain = UNNotificationAction(
            identifier: Self.remindAgainActionIdentifier,
            title: "Remind me again",
            options: []
        )

        let category = UNNotificationCategory(
            identifier: Self.categoryIdentifier,
            actions: [checked, remindAgain],
            intentIdentifiers: [],
            options: []
        )

        center.setNotificationCategories([category])
        center.delegate = self
    }

    func requestAuthorization() {
        center.requestAuthorization(options: [.alert, .badge, .sound]) { _, error in
            if let error {
                print("Notification authorization error: \(error)")
            }
        }
    }

    func sendBackSeatReminder(childName: String? = nil, delay: TimeInterval = 1) {
        let content = UNMutableNotificationContent()
        content.title = "Check the back seat"

        if let childName, !childName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            content.body = "Before walking away, make sure \(childName) and everyone else are out of the vehicle."
        } else {
            content.body = "Before walking away, make sure every child and passenger is out of the vehicle."
        }

        content.sound = .default
        content.categoryIdentifier = Self.categoryIdentifier
        content.interruptionLevel = .timeSensitive
        content.relevanceScore = 1.0

        let trigger = UNTimeIntervalNotificationTrigger(
            timeInterval: max(1, delay),
            repeats: false
        )

        center.add(
            UNNotificationRequest(
                identifier: UUID().uuidString,
                content: content,
                trigger: trigger
            )
        ) { error in
            if let error {
                print("Unable to schedule reminder: \(error)")
            }
        }
    }

    func notificationPermissionDescription(completion: @escaping (String) -> Void) {
        center.getNotificationSettings { settings in
            let description: String
            switch settings.authorizationStatus {
            case .authorized:
                description = "Authorized"
            case .denied:
                description = "Denied"
            case .notDetermined:
                description = "Not requested"
            case .provisional:
                description = "Provisional"
            case .ephemeral:
                description = "Ephemeral"
            @unknown default:
                description = "Unknown"
            }

            DispatchQueue.main.async {
                completion(description)
            }
        }
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .list, .sound])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        switch response.actionIdentifier {
        case Self.checkedActionIdentifier:
            center.removeAllPendingNotificationRequests()
            center.removeAllDeliveredNotifications()

        case Self.remindAgainActionIdentifier:
            sendBackSeatReminder(
                childName: UserDefaults.standard.string(forKey: "childName"),
                delay: 60
            )

        default:
            break
        }

        completionHandler()
    }
}
