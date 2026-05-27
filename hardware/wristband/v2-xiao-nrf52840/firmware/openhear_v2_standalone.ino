// OpenHear Wristband v2 — Standalone (No Phone) Firmware  rev 2
// Target:   Seeed Studio XIAO nRF52840 Sense
// Licence:  MIT OR Apache-2.0
//
// WHAT'S NEW vs rev 1
// -------------------
// 1. Dual DRV2605L haptic drivers — left motor (0x5A) and right motor (0x5B)
//    fire independently.  Each sound class now has a spatial encoding that
//    tells you more than just "something happened" — voice and alarm use
//    both motors, vehicle uses the left (UK road side), dog uses right, etc.
//    Ported directly from stream/haptic_mapper.py in the OpenHear repo.
//
// 2. IMU seek mode — the XIAO nRF52840 Sense has an onboard LSM6DS3
//    accelerometer/gyroscope.  When seek mode is active, the firmware tracks
//    your rotation and listens for amplitude increase as you face a sound
//    source.  When the correlation peaks, a "found it" double-tap fires on
//    both motors.  This gives directional feedback without needing a second
//    microphone.  Activate by raising then lowering the wrist sharply once.
//
// 3. Ten sound classes instead of six.  Add dog_bark, phone_ring, and
//    music_tv to your Edge Impulse project (see STANDALONE.md for the
//    updated class list and free sample sources).
//
// 4. Extended band indicators.  Sub-bass heavy sounds (vehicles, construction)
//    use a long slow pulse on the left motor.  High-frequency alerts (alarms,
//    appliances) use rapid right-biased patterns.  This encodes frequency
//    range as haptic texture so you gain a rough sense of pitch on the wrist.
//
// BEFORE COMPILING
// ----------------
// 1. Train your Edge Impulse model with the 10 classes listed below.
//    See STANDALONE.md for the updated class list and free sample sources.
// 2. Export as an Arduino library and install it.
// 3. Change the #include below to match your exported library name.
// 4. Library Manager — install (in addition to previous requirements):
//    - Seeed_Arduino_LSM6DS3   (for the onboard IMU)
// 5. If you only have ONE DRV2605L, set DUAL_MOTOR false below — the firmware
//    falls back gracefully to single-motor mode.
// 6. Upload.  Two taps = ready.

#include <Arduino.h>
#include <Wire.h>
#include <PDM.h>
#include <Adafruit_DRV2605.h>
#include <LSM6DS3.h>   // Seeed_Arduino_LSM6DS3

// Replace with your Edge Impulse exported library name:
#include "openhear-classifier_inferencing.h"

// ============================================================================
// BUILD OPTIONS
// ============================================================================
#define DUAL_MOTOR       true   // set false if you only fitted one DRV2605L
#define SEEK_MODE_ENABLE true   // set false to disable IMU direction mode

// ============================================================================
// SOUND CLASSES
// These must match the label order in your Edge Impulse project exactly.
// Train Edge Impulse with these 10 labels in this order:
//
//  0  voice       — speech, conversation
//  1  alarm       — fire alarm, smoke detector, siren, alarm clock
//  2  doorbell    — door chime, ding-dong
//  3  baby_cry    — infant crying
//  4  vehicle     — car, engine, traffic, motorcycle
//  5  appliance   — kettle, microwave, beep
//  6  dog_bark    — dog, bark, howl             (NEW)
//  7  phone_ring  — phone ringing, ringtone     (NEW)
//  8  music_tv    — music, television, radio    (NEW)
//  9  ambient     — background noise, silence   (was class 6)
//
// ============================================================================
static const uint8_t CLASS_VOICE      = 0;
static const uint8_t CLASS_ALARM      = 1;
static const uint8_t CLASS_DOORBELL   = 2;
static const uint8_t CLASS_BABY_CRY   = 3;
static const uint8_t CLASS_VEHICLE    = 4;
static const uint8_t CLASS_APPLIANCE  = 5;
static const uint8_t CLASS_DOG        = 6;
static const uint8_t CLASS_PHONE      = 7;
static const uint8_t CLASS_MUSIC_TV   = 8;
static const uint8_t CLASS_AMBIENT    = 9;

// ============================================================================
// AUDIOGRAM INTENSITY TABLE
// Derived from burgess_2021.json — baked in so no phone or JSON file needed.
// Formula: intensity = (avg_loss_dB / 100) * 180, clamped 0–180.
// To recalculate for a different person see STANDALONE.md.
// ============================================================================
static const uint8_t AUDIOGRAM_INTENSITY[10] = {
    128,   // 0 voice      — loss ~71 dB avg (500–2000 Hz)
    147,   // 1 alarm      — loss ~82 dB avg (2000–4000 Hz)
    140,   // 2 doorbell   — loss ~78 dB avg (800–2000 Hz)
    135,   // 3 baby_cry   — loss ~75 dB avg (500–4000 Hz)
     68,   // 4 vehicle    — loss ~38 dB avg (100–500 Hz)  ← partly audible
    140,   // 5 appliance  — loss ~78 dB avg (1000–3000 Hz)
     90,   // 6 dog_bark   — loss ~50 dB avg (500–1000 Hz)
    128,   // 7 phone_ring — loss ~71 dB avg (1000–2000 Hz)
    110,   // 8 music_tv   — loss ~61 dB avg (500–2000 Hz)
    100,   // 9 ambient    — broadband, low priority
};

// ============================================================================
// SPATIAL HAPTIC ENCODING
// Ported from stream/haptic_mapper.py in the OpenHear repo.
// Each sound class specifies which motor(s) fire and in what sequence.
//
// Motor conventions (worn on left wrist, viewed from above):
//   LEFT  motor (DRV2605L at I2C 0x5A, default) = closer to thumb
//   RIGHT motor (DRV2605L at I2C 0x5B, ADDR pin HIGH) = closer to little finger
//
// Spatial vocabulary:
//   BOTH  — omnidirectional / urgent
//   LEFT  — sound typically from left (vehicle in UK = road is left)
//   RIGHT — sound from right / personalised attention side
//   ALT   — alternating L/R = source direction unknown, use seek mode
// ============================================================================
static const uint8_t MOTOR_BOTH  = 0;
static const uint8_t MOTOR_LEFT  = 1;
static const uint8_t MOTOR_RIGHT = 2;
static const uint8_t MOTOR_ALT   = 3;

struct HapticPattern {
    uint8_t  routing;       // MOTOR_BOTH / LEFT / RIGHT / ALT
    uint8_t  effect_left;   // DRV2605 ROM effect ID for left motor
    uint8_t  effect_right;  // DRV2605 ROM effect ID for right motor
    uint8_t  repeats;       // times to fire
    uint16_t gap_ms;        // ms between repeats
};

static const HapticPattern HAPTIC[10] = {
    // voice      — both motors, gentle sustained buzz
    {MOTOR_BOTH,  14, 14, 1,   0},
    // alarm      — alternating L/R urgent × 3 (use seek mode to find source)
    {MOTOR_ALT,   47, 47, 3, 150},
    // doorbell   — both motors, sharp double knock
    {MOTOR_BOTH,  24, 24, 2, 100},
    // baby_cry   — right motor rising ramp (personalised attention side)
    {MOTOR_RIGHT,  1, 82, 1,   0},
    // vehicle    — left motor single long pulse (UK: road traffic from left)
    {MOTOR_LEFT,  48,  1, 1,   0},
    // appliance  — both motors short double-click (beep-like)
    {MOTOR_BOTH,  26, 26, 1,   0},
    // dog_bark   — right motor single medium pulse
    {MOTOR_RIGHT,  1, 48, 1,   0},
    // phone_ring — both motors alternating × 2 (ring cadence)
    {MOTOR_ALT,   14, 14, 2, 400},
    // music_tv   — both motors slow soft pulse × 2
    {MOTOR_BOTH,  58, 58, 2, 500},
    // ambient    — never fired (filtered before play_haptic)
    {MOTOR_BOTH,   0,  0, 0,   0},
};

// ============================================================================
// SETTINGS
// ============================================================================
static const float    CONFIDENCE_THRESHOLD = 0.75f;
static const uint32_t MIN_GAP_MS           = 1500;
static const uint32_t SEEK_WINDOW_MS       = 5000;   // seek mode timeout (ms)
static const float    SEEK_GAIN_THRESHOLD  = 1.15f;  // 15% amplitude rise = found it
static const float    WRIST_FLICK_G        = 2.2f;   // G-force to trigger seek

// ============================================================================
// GLOBALS
// ============================================================================
Adafruit_DRV2605 drv_left;    // 0x5A
Adafruit_DRV2605 drv_right;   // 0x5B
LSM6DS3          imu(I2C_MODE, 0x6A);

static int16_t   inference_buffer[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];
static bool      buffer_ready   = false;
static uint32_t  last_haptic_ms = 0;

static bool      seek_active    = false;
static uint32_t  seek_start_ms  = 0;
static float     seek_baseline  = 0.0f;
static float     seek_peak      = 0.0f;

// PDM interrupt callback
void onPDMdata() {
    int bytes = PDM.available();
    PDM.read(inference_buffer, bytes);
    buffer_ready = true;
}

// ============================================================================
// MOTOR HELPERS
// ============================================================================
bool right_motor_present() {
#if !DUAL_MOTOR
    return false;
#else
    Wire.beginTransmission(0x5B);
    return (Wire.endTransmission() == 0);
#endif
}

void init_drv(Adafruit_DRV2605 &drv) {
    drv.begin();
    drv.setMode(DRV2605_MODE_INTTRIG);
    drv.useLRA();        // LRA coin motors — better frequency response than ERM
    drv.selectLibrary(6);  // library 6 = LRA; change to 1 if using ERM motors
}

void fire_effect(Adafruit_DRV2605 &drv, uint8_t effect, uint8_t intensity) {
    drv.writeRegister8(0x17, intensity);
    drv.setWaveform(0, effect);
    drv.setWaveform(1, 0);
    drv.go();
}

void stop_all() {
    drv_left.stop();
    drv_right.stop();
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
    Wire.begin();

    init_drv(drv_left);
    init_drv(drv_right);   // harmless if right motor absent

#if SEEK_MODE_ENABLE
    imu.begin();
#endif

    // Startup confirmation: two short taps
    fire_effect(drv_left, 26, 120);
    delay(300);
    fire_effect(drv_left, 26, 120);
    delay(300);
    stop_all();

    PDM.onReceive(onPDMdata);
    PDM.begin(1, EI_CLASSIFIER_FREQUENCY);
}

// ============================================================================
// PLAY HAPTIC
// Applies spatial routing and audiogram-scaled intensity.
// ============================================================================
void play_haptic(uint8_t class_id) {
    const HapticPattern &p = HAPTIC[class_id];
    uint8_t intensity      = AUDIOGRAM_INTENSITY[class_id];
    bool    right_ok       = right_motor_present();

    for (uint8_t r = 0; r < p.repeats; r++) {
        if (p.gap_ms > 0 && r > 0) delay(p.gap_ms);

        switch (p.routing) {

            case MOTOR_BOTH:
                fire_effect(drv_left,  p.effect_left,  intensity);
                if (right_ok) fire_effect(drv_right, p.effect_right, intensity);
                break;

            case MOTOR_LEFT:
                fire_effect(drv_left, p.effect_left, intensity);
                if (right_ok) drv_right.stop();
                break;

            case MOTOR_RIGHT:
                if (right_ok) {
                    fire_effect(drv_right, p.effect_right, intensity);
                    drv_left.stop();
                } else {
                    fire_effect(drv_left, p.effect_left, intensity);  // fallback
                }
                break;

            case MOTOR_ALT:
                // Odd pulse = left, even pulse = right
                if (r % 2 == 0) {
                    fire_effect(drv_left, p.effect_left, intensity);
                    if (right_ok) drv_right.stop();
                } else {
                    if (right_ok) {
                        fire_effect(drv_right, p.effect_right, intensity);
                        drv_left.stop();
                    } else {
                        fire_effect(drv_left, p.effect_left, intensity);
                    }
                }
                break;
        }
        delay(80);
    }

    stop_all();
    last_haptic_ms = millis();
}

// ============================================================================
// SEEK MODE
//
// How it works:
//   1. A sharp wrist flick (IMU > WRIST_FLICK_G) activates seek mode.
//      A short single buzz confirms it's on.
//   2. For up to SEEK_WINDOW_MS the firmware tracks PDM amplitude.
//   3. As you rotate your body toward the sound source, the mic picks up
//      marginally more signal (body-shadow effect on an omnidirectional mic).
//   4. When amplitude climbs > SEEK_GAIN_THRESHOLD × baseline, a double-tap
//      fires on both motors: you're facing the source.
//   5. Mode exits.  If you don't find the source in time, it exits silently.
//
// This gives directional awareness with zero extra hardware.
// ============================================================================
#if SEEK_MODE_ENABLE

float rms_of_buffer() {
    int n = min((int)EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, 512);
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        float s = inference_buffer[i] / 32768.0f;
        sum += s * s;
    }
    return sqrtf(sum / n);
}

void check_seek_trigger() {
    float ax = imu.readFloatAccelX();
    float ay = imu.readFloatAccelY();
    float az = imu.readFloatAccelZ();
    float g  = sqrtf(ax*ax + ay*ay + az*az);

    if (g > WRIST_FLICK_G && !seek_active) {
        seek_active   = true;
        seek_start_ms = millis();
        seek_baseline = rms_of_buffer() + 1e-6f;
        seek_peak     = seek_baseline;
        fire_effect(drv_left, 14, 80);
        delay(60);
        stop_all();
    }
}

void update_seek() {
    if (!seek_active) return;

    if ((millis() - seek_start_ms) > SEEK_WINDOW_MS) {
        seek_active = false;
        return;
    }

    float level = rms_of_buffer();
    if (level > seek_peak) seek_peak = level;

    if (seek_peak >= seek_baseline * SEEK_GAIN_THRESHOLD) {
        // Found it
        bool right_ok = right_motor_present();
        for (uint8_t i = 0; i < 2; i++) {
            fire_effect(drv_left, 24, 160);
            if (right_ok) fire_effect(drv_right, 24, 160);
            delay(120);
            stop_all();
            delay(80);
        }
        seek_active = false;
    }
}

#endif  // SEEK_MODE_ENABLE

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
#if SEEK_MODE_ENABLE
    check_seek_trigger();
    update_seek();
#endif

    if (!buffer_ready) return;
    buffer_ready = false;

    signal_t signal;
    int err = numpy::signal_from_buffer(
        inference_buffer,
        EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE,
        &signal
    );
    if (err != 0) return;

    ei_impulse_result_t result = { 0 };
    err = run_classifier(&signal, &result, false);
    if (err != EI_IMPULSE_OK) return;

    uint8_t best_class = 0;
    float   best_score = 0.0f;
    for (uint8_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
        if (result.classification[i].value > best_score) {
            best_score = result.classification[i].value;
            best_class = i;
        }
    }

    bool confident   = best_score >= CONFIDENCE_THRESHOLD;
    bool gap_ok      = (millis() - last_haptic_ms) >= MIN_GAP_MS;
    bool not_ambient = (best_class != CLASS_AMBIENT);

    if (confident && gap_ok && not_ambient) {
        play_haptic(best_class);
    }

    delay(10);
}
