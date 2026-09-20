import Combine
import CoreLocation
import CoreMotion
import Foundation

final class DriveMonitor: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published private(set) var state: DriveState = .idle
    @Published private(set) var locationPermission = "Not requested"
    @Published private(set) var motionPermission = "Not requested"
    @Published private(set) var notificationPermission = "Not requested"
    @Published private(set) var lastEvent = "Monitoring has not started."
    @Published private(set) var distanceFromParkingCandidate: CLLocationDistance = 0
    @Published var enabled: Bool {
        didSet {
            UserDefaults.standard.set(enabled, forKey: Keys.enabled)
            enabled ? startMonitoring() : stopMonitoring()
        }
    }

    private enum Keys {
        static let enabled = "reminderEnabled"
        static let state = "driveState"
        static let candidateLatitude = "candidateLatitude"
        static let candidateLongitude = "candidateLongitude"
        static let candidateDate = "candidateDate"
    }

    private let locationManager = CLLocationManager()
    private let motionManager = CMMotionActivityManager()
    private let notificationManager: NotificationManager
    private let motionQueue: OperationQueue = {
        let queue = OperationQueue()
        queue.name = "BackSeatReminder.Motion"
        queue.qualityOfService = .utility
        queue.maxConcurrentOperationCount = 1
        return queue
    }()

    private var parkingCandidateLocation: CLLocation?
    private var parkingCandidateDate: Date?
    private var lastKnownLocation: CLLocation?

    private let drivingSpeedThreshold: CLLocationSpeed = 5.0
    private let stoppedSpeedThreshold: CLLocationSpeed = 1.5
    private let walkingAwayDistance: CLLocationDistance = 20.0
    private let fallbackWalkingDistance: CLLocationDistance = 35.0

    init(notificationManager: NotificationManager) {
        self.notificationManager = notificationManager
        self.enabled = UserDefaults.standard.bool(forKey: Keys.enabled)
        super.init()

        locationManager.delegate = self
        locationManager.activityType = .automotiveNavigation
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.distanceFilter = 10
        locationManager.pausesLocationUpdatesAutomatically = true

        restoreState()
        refreshPermissionDescriptions()

        if enabled {
            startMonitoring()
        }
    }

    func requestPermissions() {
        notificationManager.requestAuthorization()

        switch locationManager.authorizationStatus {
        case .notDetermined:
            locationManager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse:
            locationManager.requestAlwaysAuthorization()
        case .authorizedAlways:
            startMonitoring()
        case .restricted, .denied:
            break
        @unknown default:
            break
        }

        requestMotionAuthorization()
        refreshPermissionDescriptions()
    }

    func refreshPermissionDescriptions() {
        locationPermission = Self.locationAuthorizationDescription(locationManager.authorizationStatus)
        motionPermission = Self.motionAuthorizationDescription(CMMotionActivityManager.authorizationStatus())

        notificationManager.notificationPermissionDescription { [weak self] description in
            self?.notificationPermission = description
        }
    }

    func sendTestReminder() {
        notificationManager.sendBackSeatReminder(
            childName: UserDefaults.standard.string(forKey: "childName")
        )
        lastEvent = "Sent a test reminder."
    }

    private func startMonitoring() {
        guard enabled else { return }

        refreshPermissionDescriptions()

        let status = locationManager.authorizationStatus
        guard status == .authorizedAlways || status == .authorizedWhenInUse else {
            lastEvent = "Location permission is required before monitoring can start."
            return
        }

        locationManager.startMonitoringSignificantLocationChanges()
        lastEvent = "Low-power drive monitoring is active."

        if state == .driving || state == .parkingCandidate || state == .walkingAway {
            beginPreciseLocationUpdates()
        }
    }

    private func stopMonitoring() {
        locationManager.stopMonitoringSignificantLocationChanges()
        locationManager.stopUpdatingLocation()
        locationManager.allowsBackgroundLocationUpdates = false
        motionManager.stopActivityUpdates()

        transition(to: .idle, event: "Reminder monitoring is off.")
        clearParkingCandidate()
    }

    private func beginPreciseLocationUpdates() {
        guard enabled else { return }
        locationManager.allowsBackgroundLocationUpdates = true
        locationManager.startUpdatingLocation()
    }

    private func finishPreciseLocationUpdates() {
        locationManager.stopUpdatingLocation()
        locationManager.allowsBackgroundLocationUpdates = false

        if enabled {
            locationManager.startMonitoringSignificantLocationChanges()
        }
    }

    private func requestMotionAuthorization() {
        guard CMMotionActivityManager.isActivityAvailable() else {
            motionPermission = "Unavailable"
            return
        }

        let now = Date()
        motionManager.queryActivityStarting(
            from: now.addingTimeInterval(-60),
            to: now,
            to: motionQueue
        ) { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.refreshPermissionDescriptions()
            }
        }
    }

    private func evaluate(location: CLLocation) {
        lastKnownLocation = location

        queryRecentMotion { [weak self] activity in
            guard let self else { return }

            DispatchQueue.main.async {
                self.evaluate(location: location, activity: activity)
            }
        }
    }

    private func evaluate(location: CLLocation, activity: CMMotionActivity?) {
        guard enabled else { return }

        let speed = max(location.speed, 0)
        let automotive = activity?.automotive == true
        let walking = activity?.walking == true || activity?.running == true

        switch state {
        case .idle, .reminderSent:
            if automotive || speed >= drivingSpeedThreshold {
                clearParkingCandidate()
                transition(to: .driving, event: "Driving detected.")
                beginPreciseLocationUpdates()
            }

        case .driving:
            if speed <= stoppedSpeedThreshold && !automotive {
                setParkingCandidate(location)
                transition(to: .parkingCandidate, event: "Vehicle appears to have stopped.")
            }

        case .parkingCandidate:
            if automotive || speed >= drivingSpeedThreshold {
                clearParkingCandidate()
                transition(to: .driving, event: "Vehicle started moving again.")
                return
            }

            guard let candidate = parkingCandidateLocation else {
                setParkingCandidate(location)
                return
            }

            let distance = location.distance(from: candidate)
            distanceFromParkingCandidate = distance

            if walking && distance >= walkingAwayDistance {
                transition(to: .walkingAway, event: "Walking away from the parking location.")
                fireReminder()
            } else if activity == nil,
                      distance >= fallbackWalkingDistance,
                      Date().timeIntervalSince(parkingCandidateDate ?? Date()) >= 20,
                      speed < 3.0 {
                transition(to: .walkingAway, event: "Moved away from the parking location.")
                fireReminder()
            }

        case .walkingAway:
            fireReminder()
        }
    }

    private func fireReminder() {
        guard state != .reminderSent else { return }

        notificationManager.sendBackSeatReminder(
            childName: UserDefaults.standard.string(forKey: "childName")
        )

        transition(to: .reminderSent, event: "Back-seat reminder sent.")
        finishPreciseLocationUpdates()
        clearParkingCandidate()
    }

    private func setParkingCandidate(_ location: CLLocation) {
        parkingCandidateLocation = location
        parkingCandidateDate = Date()
        distanceFromParkingCandidate = 0
        persistState()
    }

    private func clearParkingCandidate() {
        parkingCandidateLocation = nil
        parkingCandidateDate = nil
        distanceFromParkingCandidate = 0

        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: Keys.candidateLatitude)
        defaults.removeObject(forKey: Keys.candidateLongitude)
        defaults.removeObject(forKey: Keys.candidateDate)
    }

    private func queryRecentMotion(completion: @escaping (CMMotionActivity?) -> Void) {
        guard CMMotionActivityManager.isActivityAvailable() else {
            completion(nil)
            return
        }

        let end = Date()
        let start = end.addingTimeInterval(-120)

        motionManager.queryActivityStarting(
            from: start,
            to: end,
            to: motionQueue
        ) { activities, _ in
            let latest = activities?
                .filter { $0.confidence != .low }
                .max(by: { $0.startDate < $1.startDate })

            completion(latest)
        }
    }

    private func transition(to newState: DriveState, event: String) {
        state = newState
        lastEvent = event
        persistState()
    }

    private func persistState() {
        let defaults = UserDefaults.standard
        defaults.set(state.rawValue, forKey: Keys.state)

        if let candidate = parkingCandidateLocation {
            defaults.set(candidate.coordinate.latitude, forKey: Keys.candidateLatitude)
            defaults.set(candidate.coordinate.longitude, forKey: Keys.candidateLongitude)
        }

        if let parkingCandidateDate {
            defaults.set(parkingCandidateDate, forKey: Keys.candidateDate)
        }
    }

    private func restoreState() {
        let defaults = UserDefaults.standard

        if let raw = defaults.string(forKey: Keys.state),
           let restored = DriveState(rawValue: raw) {
            state = restored
        }

        if defaults.object(forKey: Keys.candidateLatitude) != nil,
           defaults.object(forKey: Keys.candidateLongitude) != nil {
            parkingCandidateLocation = CLLocation(
                latitude: defaults.double(forKey: Keys.candidateLatitude),
                longitude: defaults.double(forKey: Keys.candidateLongitude)
            )
        }

        parkingCandidateDate = defaults.object(forKey: Keys.candidateDate) as? Date
    }

    private static func locationAuthorizationDescription(_ status: CLAuthorizationStatus) -> String {
        switch status {
        case .authorizedAlways:
            return "Always"
        case .authorizedWhenInUse:
            return "While Using"
        case .denied:
            return "Denied"
        case .restricted:
            return "Restricted"
        case .notDetermined:
            return "Not requested"
        @unknown default:
            return "Unknown"
        }
    }

    private static func motionAuthorizationDescription(_ status: CMAuthorizationStatus) -> String {
        switch status {
        case .authorized:
            return "Authorized"
        case .denied:
            return "Denied"
        case .restricted:
            return "Restricted"
        case .notDetermined:
            return "Not requested"
        @unknown default:
            return "Unknown"
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        refreshPermissionDescriptions()

        if manager.authorizationStatus == .authorizedWhenInUse {
            manager.requestAlwaysAuthorization()
        }

        if enabled,
           manager.authorizationStatus == .authorizedAlways ||
           manager.authorizationStatus == .authorizedWhenInUse {
            startMonitoring()
        }
    }

    func locationManager(
        _ manager: CLLocationManager,
        didUpdateLocations locations: [CLLocation]
    ) {
        guard let latest = locations.last else { return }
        guard latest.horizontalAccuracy >= 0, latest.horizontalAccuracy <= 100 else { return }

        evaluate(location: latest)
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        lastEvent = "Location error: \(error.localizedDescription)"
    }

    #if DEBUG
    func debugSimulateDriving() {
        transition(to: .driving, event: "DEBUG: driving simulated.")
    }

    func debugSimulateParking() {
        let base = lastKnownLocation ?? CLLocation(latitude: 27.2730, longitude: -80.3582)
        setParkingCandidate(base)
        transition(to: .parkingCandidate, event: "DEBUG: parking simulated.")
    }

    func debugSimulateWalkingAway() {
        transition(to: .walkingAway, event: "DEBUG: walking away simulated.")
        fireReminder()
    }
    #endif
}
