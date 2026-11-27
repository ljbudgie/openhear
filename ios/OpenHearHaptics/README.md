# OpenHear Haptics for iPhone

OpenHear Haptics lets you feel the nine OpenHear wristband vibration patterns on an iPhone, through its Taptic Engine. You can play each pattern, and practise naming them.

It is for environmental sound awareness only. It is not a hearing aid and not a medical device. This version does not use the microphone and does not recognise sounds. It plays and teaches the patterns.

The "Vehicle warning" pattern is a practice pattern only. It is not a safety feature and must not be relied on to warn of a vehicle.

## Status

This app has not yet been built or run in Xcode, in the Simulator or on an iPhone. The pattern table, packet format and practice scoring have been compiled and tested with Swift on Linux. The screens, Core Haptics and Bluetooth code need Apple's tools, so they will be checked for the first time when you follow the steps below.

## What is in the app

1. **Patterns.** The nine patterns, each with its name, a one-line description, a small left and right timing strip, and a play button. Tap a row to feel it. The strip lights up as it plays.
2. **Practice.** "Name the sound". The app plays a random pattern with nothing on screen to give it away. You choose one of the nine names. It tells you if you were right and what the answer was, and "Feel it again" plays it again. It keeps, for each pattern, how many tries, how many right, and the sound you most often mix it up with. These results stay on the iPhone only. There is a reset button.
3. **Settings.** The strength slider (0 to 255, default 200, as on the wristband), the three left and right sharpness values, and the wristband section.

## The nine patterns

Each step is (left motor, right motor, milliseconds). (0,0,ms) is a pause. They are copied from `wristband/openhear_firmware.py`.

| Id | Sound | Steps | Total |
|---|---|---|---|
| 1 | Someone speaking | (1,1,200)(0,0,100) x3 | 900 ms |
| 2 | Doorbell | (1,1,50)(0,0,50) x2 | 200 ms |
| 3 | Alarm | (1,0,30)(0,0,30)(0,1,30)(0,0,30) x4 | 480 ms |
| 4 | Dog barking | (0,1,150) | 150 ms |
| 5 | Vehicle warning | (1,0,300) | 300 ms |
| 6 | Music or TV | (1,1,500)(0,0,500) x2 | 2000 ms |
| 7 | Knock | (1,1,80)(0,0,40)(1,1,40) | 160 ms |
| 8 | Baby crying | (1,1,60)(0,0,40) x4 | 400 ms |
| 9 | Phone ringing | (1,0,100)(0,0,80)(0,1,100)(0,0,80) x3 | 1080 ms |

The table lives in `OpenHearHaptics/Model/Patterns.swift`. The tests in `OpenHearHapticsTests/PatternsTests.swift` check every step and every total. `Scripts/check_patterns.py` runs the firmware's own pattern code and checks it gives the same steps:

```
python3 ios/OpenHearHaptics/Scripts/check_patterns.py
```

## Left and right on a phone with one motor

The wristband has two motors. An iPhone has one. So the app shows left and right as different textures, using Core Haptics sharpness:

1. Left motor only: sharpness 0.2 (soft, dull).
2. Right motor only: sharpness 0.9 (crisp).
3. Both motors: sharpness 0.5.

This is a design choice to test, not part of the wristband firmware. The three defaults are named constants in `OpenHearHaptics/Model/HapticPlan.swift` (`leftOnlySharpness`, `rightOnlySharpness`, `bothSharpness`). You can also change them in Settings while you try them, and put them back with "Restore 0.2, 0.9 and 0.5".

Strength works as on the wristband. The phone's vibration strength is the slider value divided by 255.

If the vibration engine stops or resets (for example after a phone call), the app restarts it. A pattern that was cut off part way is played again from the start. If the phone cannot play custom vibrations, the app says so on screen.

## The wristband (switched off until you need it)

Bluetooth is built in but not used until you tap **Connect** in Settings. The app does not even ask for Bluetooth permission before then. Phone vibrations work with Bluetooth off.

1. Tap **Connect**. The app looks for a device that advertises the Nordic UART service (6E400001-B5A3-F393-E0A9-E50E24DCCA9E), or whose name starts with "OpenHear" or "Bangle". It stops looking after 20 seconds.
2. Once connected, it writes to the UART characteristic that accepts writes. It picks by what the characteristic allows, not by its number, because a micro:bit and a Bangle.js use different ones.
3. Turn on **Play on wristband too**. It is off every time the app opens. Each pattern then also sends 3 bytes: sound class id, strength 0 to 255, pattern id. Class id and pattern id are both the pattern's number, 1 to 9.
4. **Send onset ramp to wristband** sends the control packet 255, ramp in milliseconds divided by 2, 1. The ramp can be 0 to 510 ms.
5. The last 20 packets sent are listed in hex, newest first.

## Running it on your iPhone

You need a Mac, your iPhone and a USB cable. A free Apple ID is enough.

### On the Mac, once

1. Install Xcode from the Mac App Store. Open it once and let it install its extra components.
2. Install Homebrew if you do not have it, from https://brew.sh
3. Install XcodeGen, which makes the Xcode project from `project.yml`:
   ```
   brew install xcodegen
   ```
4. Get the code and make the project:
   ```
   git clone https://github.com/ljbudgie/openhear.git
   cd openhear
   git checkout ios-haptics-app
   cd ios/OpenHearHaptics
   xcodegen generate
   open OpenHearHaptics.xcodeproj
   ```
   Run `xcodegen generate` again whenever `project.yml` changes or files are added. The `.xcodeproj` it makes is not kept in git.
5. In Xcode, go to **Xcode > Settings > Accounts**, press **+**, choose **Apple ID** and sign in with your free Apple ID.
6. In the left sidebar click the blue **OpenHearHaptics** project, then the **OpenHearHaptics** target, then **Signing & Capabilities**. Leave **Automatically manage signing** ticked and choose your name ("Personal Team") under **Team**.
   If Xcode says the bundle identifier is not available, change it slightly, for example add `.lj` to the end, and try again.

### On the iPhone, once

1. Plug the iPhone into the Mac and tap **Trust** if it asks.
2. Turn on Developer Mode: **Settings > Privacy & Security > Developer Mode**, switch it on, and let the iPhone restart. Confirm when it asks. (The Developer Mode option appears after the iPhone has been connected to Xcode.)

### Each time you run it

1. In Xcode, choose your iPhone from the device menu at the top of the window.
2. Press the **Run** button (the triangle), or Command R.
3. The first time, the iPhone may say the developer is not trusted. Go to **Settings > General > VPN & Device Management**, tap your Apple ID under Developer App, and tap **Trust**. Then run it again from Xcode.

### The 7 day limit

With a free Apple ID, an app you install from Xcode stops opening after 7 days. To keep using it, plug the iPhone in and press **Run** in Xcode again. Your settings and practice results are kept. A paid Apple Developer account removes this limit, but you do not need one.

## Building and testing from the command line (Mac only)

The Simulator has no vibration motor, so on the Simulator the app shows the "cannot play custom vibrations" notice. That is expected.

```
cd ios/OpenHearHaptics
xcodegen generate
xcrun simctl list devices available | grep iPhone
xcodebuild -project OpenHearHaptics.xcodeproj -scheme OpenHearHaptics \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  CODE_SIGNING_ALLOWED=NO build test
```

Replace `iPhone 16` with any iPhone name from the list.

## Files

1. `project.yml`: the XcodeGen project definition. iOS 17 or later, iPhone only, portrait.
2. `Support/Info.plist`: app settings, including the Bluetooth message "OpenHear connects to your wristband to play sound patterns on it."
3. `OpenHearHaptics/Model/`: the pattern table, the haptic plan and sharpness constants, the packet format and the practice scores. No Apple-only frameworks, so these build and test anywhere.
4. `OpenHearHaptics/Haptics/HapticPlayer.swift`: Core Haptics playback.
5. `OpenHearHaptics/Bluetooth/WristbandBluetooth.swift`: the wristband link.
6. `OpenHearHaptics/Views/`: the Patterns, Practice and Settings screens. All text uses Dynamic Type and every control has a VoiceOver label.
7. `OpenHearHapticsTests/`: XCTests for the patterns, packets and practice scores.
8. `Scripts/check_patterns.py`: checks the table against the firmware.
