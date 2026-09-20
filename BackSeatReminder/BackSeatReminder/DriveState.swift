import Foundation

enum DriveState: String, Codable, CaseIterable {
    case idle = "Idle"
    case driving = "Driving"
    case parkingCandidate = "Parking candidate"
    case walkingAway = "Walking away"
    case reminderSent = "Reminder sent"
}
