import SwiftUI

struct ContentView: View {
    @ObservedObject var monitor: DriveMonitor
    @AppStorage("childName") private var childName = ""

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Toggle(
                        "Child reminder",
                        isOn: Binding(
                            get: { monitor.enabled },
                            set: { monitor.enabled = $0 }
                        )
                    )

                    Text("When enabled, the app looks for a drive ending and then for you walking away before sending a reminder.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Section("Reminder") {
                    TextField("Child name (optional)", text: $childName)

                    Button("Send Test Reminder") {
                        monitor.sendTestReminder()
                    }
                }

                Section("Status") {
                    LabeledContent("State", value: monitor.state.rawValue)
                    LabeledContent("Last event", value: monitor.lastEvent)

                    if monitor.state == .parkingCandidate {
                        LabeledContent(
                            "Distance from parked location",
                            value: "\(Int(monitor.distanceFromParkingCandidate)) m"
                        )
                    }
                }

                Section("Permissions") {
                    LabeledContent("Location", value: monitor.locationPermission)
                    LabeledContent("Motion", value: monitor.motionPermission)
                    LabeledContent("Notifications", value: monitor.notificationPermission)

                    Button("Request / Refresh Permissions") {
                        monitor.requestPermissions()
                    }
                }

                #if DEBUG
                Section("Debug") {
                    Button("Simulate Driving") {
                        monitor.debugSimulateDriving()
                    }

                    Button("Simulate Parking") {
                        monitor.debugSimulateParking()
                    }

                    Button("Simulate Walking Away + Reminder") {
                        monitor.debugSimulateWalkingAway()
                    }
                }
                #endif

                Section("Safety") {
                    Text("This app is a supplemental reminder. iOS can delay or suppress background work and notifications, so it must not be treated as a guaranteed child-presence detection system.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Back Seat Reminder")
            .onAppear {
                monitor.refreshPermissionDescriptions()
            }
        }
    }
}
