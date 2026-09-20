# Back Seat Reminder

An opt-in iPhone safety reminder that attempts to recognize this sequence:

1. The phone is traveling in a vehicle.
2. The vehicle stops.
3. The user begins walking away from the parking location.
4. The app sends a **Time Sensitive** "Check the back seat" notification.

This is an early prototype. It intentionally keeps detection and state on-device and does not require an account or server.

## Current architecture

- SwiftUI
- Core Location
- Core Motion
- UserNotifications
- UserDefaults for small local state restoration
- Significant-location monitoring while idle
- Higher-accuracy location updates only during an active drive / parking transition

The state machine is:

```
Idle
  -> Driving
  -> Parking candidate
  -> Walking away
  -> Reminder sent
```

If the vehicle begins moving again from a parking candidate, the state returns to Driving.

## Why both location and motion?

Location provides speed, distance from the candidate parking point, and a background wake-up path. Core Motion helps distinguish automotive movement from walking/running so a long stoplight does not immediately become a reminder.

Core Motion history can be delayed, so the prototype also uses conservative speed/distance fallbacks.

## Setup

This repository uses [XcodeGen](https://github.com/yonaskolb/XcodeGen) so the project file can be generated instead of hand-maintained.

On the Mac:

```bash
cd BackSeatReminder
brew install xcodegen
xcodegen generate
open BackSeatReminder.xcodeproj
```

In Xcode:

1. Select the **BackSeatReminder** target.
2. Open **Signing & Capabilities**.
3. Choose your Apple Developer Team.
4. Build to a physical iPhone.
5. Enable the reminder and grant notifications, motion, and location permissions.
6. For reliable background trip detection, allow **Always** location access when iOS offers it.

The Debug build includes buttons to simulate the major state transitions without taking a real drive.

## Detection thresholds

The initial tuning values live in `DriveMonitor.swift`:

- driving speed: 5 m/s
- stopped speed: 1.5 m/s
- walking-away distance: 20 m
- no-motion fallback distance: 35 m

These are starting points, not final production values. Real-world drive testing is expected to change them.

## Privacy

The prototype:

- does not create an account
- does not upload location
- does not include analytics
- does not include advertising
- stores only minimal state required to survive an app relaunch

## Safety limitation

This app is a **supplemental reminder**, not a child-detection device and not a life-safety guarantee. iOS background execution, permissions, sensor availability, battery management, and notification settings can all affect delivery.

A production release should measure missed detections and false positives across many real trips before making any reliability claims.
