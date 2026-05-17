// OpenHear Wristband v2 - "Premium Slim" firmware
// Target board:  Seeed Studio XIAO nRF52840 (or XIAO nRF52840 Sense)
// Toolchain:     Arduino IDE + Seeed nRF52 mbed-enabled BSP
// Radio stack:   NimBLE-Arduino (preferred) OR Adafruit Bluefruit nRF52 BLE
// Haptic stack:  Adafruit DRV2605 Library (open-source, MIT)
//
// Licence: MIT OR Apache-2.0 (matches v1 firmware)
//
// CONTRACT WITH THE REST OF THE OPENHEAR STACK (DO NOT CHANGE):
//   - Same 3-byte BLE haptic packet  [sound_class_id, intensity, pattern_id]
//   - Same 7 YAMNet sound classes (IDs 0..6) + audiogram JSON intensity weighting
//   - BLE is companion-only; on-wrist haptics MUST never depend on the radio
//   - Local-first, Burgess-Principle: no raw audio leaves the device
//
// This sketch keeps the high-level architecture identical to
//   wristband/openhear_firmware.py and hardware/wristband/firmware/openhear_firmware_v1.py
// so the existing classifier, audiogram, and phone tools stream into it unchanged.
//
// Pin map (default XIAO nRF52840 Sense, no-solder via Seeed Expansion Base):
//   D4 / D5  -> I2C SDA / SCL  (DRV2605L + optional TCA9548A)
//   D0       -> optional GPIO IRQ from a future second DRV2605L bank
//   onboard  -> PDM mic (Sense only), IMU LSM6DS3TR-C (Sense only)
//   VBUS     -> USB-C 5 V (also routed to magnetic pogo dock pads)
//
// Sleep strategy: System OFF between BLE events; DRV2605L is put in standby
// after every effect; LED is never driven in production builds.

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_DRV2605.h>

// ---- BLE backend selection -------------------------------------------------
// Define exactly one of these before the include.
#define OPENHEAR_USE_NIMBLE 1
// #define OPENHEAR_USE_BLUEFRUIT 1

#if defined(OPENHEAR_USE_NIMBLE)
  #include <NimBLEDevice.h>
#elif defined(OPENHEAR_USE_BLUEFRUIT)
  #include <bluefruit.h>
#else
  #error "Define OPENHEAR_USE_NIMBLE or OPENHEAR_USE_BLUEFRUIT"
#endif

// ============================================================================
// Constants - must match the rest of OpenHear
// ============================================================================
static const char*   DEVICE_NAME            = "OpenHear-v2";
static const uint8_t MAX_INTENSITY          = 180;   // matches v1 cap
static const uint8_t NUM_SOUND_CLASSES      = 7;     // YAMNet 7-class head
static const uint8_t V0_COMPAT_PATTERN      = 240;   // matches v1 firmware
static const uint32_t IDLE_SLEEP_AFTER_MS   = 8000;  // enter low-power after silence

// OpenHear haptic service - keep these UUIDs stable across firmware versions.
// They are the same UUIDs published by the v1 Python firmware reference.
#define OPENHEAR_SVC_UUID    "6f68656172-0000-1000-8000-00805f9b34fb"
#define OPENHEAR_PKT_CHR_UUID "6f68656172-0001-1000-8000-00805f9b34fb"  // write: 3-byte packet
#define OPENHEAR_CFG_CHR_UUID "6f68656172-0002-1000-8000-00805f9b34fb"  // write: [actuator_count, intensity_cap]

// ============================================================================
// Haptic effect map - one open-source DRV2605 ROM effect per sound class.
// Index = sound_class_id (0..6). Tune to your audiogram JSON.
//
// Class IDs MUST match the YAMNet 7-class head defined in
// yamnet_classifier.py / audiogram/*.json so the phone and the wrist agree.
// ============================================================================
struct ClassEffect {
    const char* label;           // human label, for debug only
    uint8_t     primary_effect;  // DRV2605 ROM library effect 1..123
    uint8_t     accent_effect;   // optional second effect played on a 2nd LRA
    uint8_t     repeat;          // number of times to play primary
    uint8_t     min_intensity;   // floor (avoid sub-threshold buzz)
};

static const ClassEffect CLASS_EFFECTS[NUM_SOUND_CLASSES] = {
    // id 0: speech            - soft, sustained
    { "speech",          14, 17, 1,  40 },  // "Strong buzz 60%" + "Strong click 60%"
    // id 1: alarm/siren       - sharp, urgent, repeated
    { "alarm",           47,  1, 3,  80 },  // "Buzz 1 - 100%" x3
    // id 2: doorbell/knock    - double-click feel
    { "doorbell",        24, 27, 2,  60 },  // "Sharp click 100%" + "Short double click strong"
    // id 3: baby cry          - long ramp
    { "baby_cry",        82, 70, 2,  70 },  // "Transition ramp up long sharp"
    // id 4: vehicle/horn      - hard pulse
    { "vehicle",         48,  3, 2,  90 },  // "Buzz 2 - 80%"
    // id 5: appliance beep    - triple short tick
    { "appliance",       26, 27, 3,  40 },  // "Short double click medium"
    // id 6: ambient/other     - gentle awareness pulse
    { "ambient",         58,  0, 1,  30 },  // "Long buzz no stop"
};

// ============================================================================
// Globals
// ============================================================================
Adafruit_DRV2605 g_drv;
volatile bool    g_drv_present     = false;
volatile uint8_t g_intensity_cap   = MAX_INTENSITY;
volatile uint8_t g_actuator_count  = 2;
volatile uint32_t g_last_event_ms  = 0;

// ============================================================================
// Haptic primitives
// ============================================================================
static void drv_play_effect(uint8_t slot, uint8_t effect_id) {
    if (!g_drv_present || effect_id == 0) return;
    g_drv.setWaveform(slot, effect_id);
}

static void drv_terminate(uint8_t slot) {
    if (!g_drv_present) return;
    g_drv.setWaveform(slot, 0);  // 0 = end-of-sequence marker
}

static void drv_go() {
    if (!g_drv_present) return;
    g_drv.go();
}

// Scale intensity (0..255) onto the DRV2605 overdrive register so quiet
// classifier outputs still feel like a gentle tap and never below threshold.
static void drv_set_intensity(uint8_t intensity) {
    if (!g_drv_present) return;
    uint8_t capped = (intensity > g_intensity_cap) ? g_intensity_cap : intensity;
    g_drv.setRealtimeValue(capped);  // also useful for RTP mode tests
}

// Render one OpenHear 3-byte packet into DRV2605 waveform slots.
static void render_packet(uint8_t sound_class_id, uint8_t intensity, uint8_t pattern_id) {
    g_last_event_ms = millis();

    if (intensity == 0 || pattern_id == 0) {
        // Explicit silence packet
        if (g_drv_present) g_drv.stop();
        return;
    }

    // v0 micro:bit-compatible "shim" pattern -> single tap on actuator 0
    if (pattern_id == V0_COMPAT_PATTERN) {
        drv_play_effect(0, 1);          // "Strong click 100%"
        drv_terminate(1);
        drv_set_intensity(intensity);
        drv_go();
        return;
    }

    if (sound_class_id >= NUM_SOUND_CLASSES) sound_class_id = NUM_SOUND_CLASSES - 1;
    const ClassEffect& fx = CLASS_EFFECTS[sound_class_id];

    uint8_t effective = (intensity < fx.min_intensity) ? fx.min_intensity : intensity;
    drv_set_intensity(effective);

    uint8_t slot = 0;
    for (uint8_t r = 0; r < fx.repeat && slot < 7; ++r, ++slot) {
        drv_play_effect(slot, fx.primary_effect);
    }
    if (fx.accent_effect != 0 && slot < 7) {
        drv_play_effect(slot++, fx.accent_effect);
    }
    if (slot < 8) drv_terminate(slot);

    drv_go();
}

// ============================================================================
// Power management - keep all-day battery target
// ============================================================================
static void enter_low_power_if_idle() {
    if (millis() - g_last_event_ms < IDLE_SLEEP_AFTER_MS) return;
    if (g_drv_present) g_drv.stop();
    // mbed-style nrf52: wait-for-event keeps BLE radio listening at ~20 uA
    __WFE();
    __SEV();
    __WFE();
}

// ============================================================================
// BLE - NimBLE backend
// ============================================================================
#if defined(OPENHEAR_USE_NIMBLE)

class PacketCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* chr) override {
        std::string v = chr->getValue();
        if (v.size() < 3) return;
        render_packet((uint8_t)v[0], (uint8_t)v[1], (uint8_t)v[2]);
    }
};

class ConfigCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* chr) override {
        std::string v = chr->getValue();
        if (v.size() >= 1) g_actuator_count = (uint8_t)v[0];
        if (v.size() >= 2) g_intensity_cap  = (uint8_t)v[1] > MAX_INTENSITY
                                              ? MAX_INTENSITY : (uint8_t)v[1];
    }
};

static void ble_begin() {
    NimBLEDevice::init(DEVICE_NAME);
    // Low TX power; companion is at arm's length. NimBLE-Arduino on nRF52
    // accepts dBm directly (range roughly -40..+8). On the ESP32 build of
    // NimBLE the same call accepts the ESP_PWR_LVL_* enum; using the dBm
    // overload keeps this sketch platform-portable on the XIAO nRF52840.
    NimBLEDevice::setPower(-12);
    NimBLEServer* server = NimBLEDevice::createServer();
    NimBLEService* svc   = server->createService(OPENHEAR_SVC_UUID);

    NimBLECharacteristic* pkt = svc->createCharacteristic(
        OPENHEAR_PKT_CHR_UUID,
        NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR);
    pkt->setCallbacks(new PacketCallbacks());

    NimBLECharacteristic* cfg = svc->createCharacteristic(
        OPENHEAR_CFG_CHR_UUID,
        NIMBLE_PROPERTY::WRITE);
    cfg->setCallbacks(new ConfigCallbacks());

    svc->start();
    NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
    adv->addServiceUUID(OPENHEAR_SVC_UUID);
    adv->setName(DEVICE_NAME);
    adv->start();
}

#elif defined(OPENHEAR_USE_BLUEFRUIT)
// Minimal Bluefruit alternative left as a stub so users can swap stacks.
static BLEService        g_svc(OPENHEAR_SVC_UUID);
static BLECharacteristic g_pkt(OPENHEAR_PKT_CHR_UUID);
static BLECharacteristic g_cfg(OPENHEAR_CFG_CHR_UUID);

static void pkt_write_cb(uint16_t, BLECharacteristic* chr, uint8_t* data, uint16_t len) {
    if (len < 3) return;
    render_packet(data[0], data[1], data[2]);
}
static void cfg_write_cb(uint16_t, BLECharacteristic* chr, uint8_t* data, uint16_t len) {
    if (len >= 1) g_actuator_count = data[0];
    if (len >= 2) g_intensity_cap  = data[1] > MAX_INTENSITY ? MAX_INTENSITY : data[1];
}

static void ble_begin() {
    Bluefruit.begin();
    Bluefruit.setTxPower(-12);
    Bluefruit.setName(DEVICE_NAME);
    g_svc.begin();
    g_pkt.setProperties(CHR_PROPS_WRITE | CHR_PROPS_WRITE_WO_RESP);
    g_pkt.setPermission(SECMODE_OPEN, SECMODE_OPEN);
    g_pkt.setFixedLen(3);
    g_pkt.setWriteCallback(pkt_write_cb);
    g_pkt.begin();
    g_cfg.setProperties(CHR_PROPS_WRITE);
    g_cfg.setPermission(SECMODE_OPEN, SECMODE_OPEN);
    g_cfg.setMaxLen(2);
    g_cfg.setWriteCallback(cfg_write_cb);
    g_cfg.begin();
    Bluefruit.Advertising.addService(g_svc);
    Bluefruit.Advertising.addName();
    Bluefruit.Advertising.restartOnDisconnect(true);
    Bluefruit.Advertising.start(0);
}
#endif

// ============================================================================
// Setup / loop
// ============================================================================
void setup() {
    // Serial is optional on a sealed wearable; safe to leave disabled to save power.
    Wire.begin();
    Wire.setClock(400000);

    g_drv_present = g_drv.begin();
    if (g_drv_present) {
        g_drv.selectLibrary(1);                  // ERM library 1, switch to 6 for LRA
        g_drv.useLRA();                          // OpenHear v2 default actuator
        g_drv.setMode(DRV2605_MODE_INTTRIG);     // internal trigger via .go()
    }

    ble_begin();
    g_last_event_ms = millis();
}

void loop() {
    // BLE event handling for both backends is interrupt/callback driven.
    enter_low_power_if_idle();
    delay(2);
}
