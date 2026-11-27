import CoreBluetooth
import Foundation

/// Bluetooth link to an OpenHear wristband (micro:bit) or a Bangle.js.
///
/// Nothing Bluetooth happens until connect() is called: the central manager
/// is only created then, so the app does not even ask for Bluetooth
/// permission before LJ taps Connect. Phone vibrations never depend on this.
final class WristbandBluetooth: NSObject, ObservableObject {
    enum Status: Equatable {
        case off
        case waitingForBluetooth
        case scanning
        case connecting(String)
        case connected(String)
        case problem(String)

        var text: String {
            switch self {
            case .off: return "Not connected. Bluetooth is not in use."
            case .waitingForBluetooth: return "Waiting for Bluetooth."
            case .scanning: return "Looking for a wristband."
            case .connecting(let name): return "Connecting to \(name)."
            case .connected(let name): return "Connected to \(name)."
            case .problem(let message): return message
            }
        }
    }

    /// Nordic UART service, used by the OpenHear micro:bit firmware and Bangle.js.
    static let uartService = CBUUID(string: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    /// The usual UART write characteristic. Only a preference: the writable
    /// characteristic is picked by its properties, because a micro:bit and a
    /// Bangle.js do not agree on which one receives.
    static let preferredWriteCharacteristic = CBUUID(string: "6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
    static let namePrefixes = ["OpenHear", "Bangle"]
    static let scanTimeoutSeconds: TimeInterval = 20

    @Published private(set) var status: Status = .off
    @Published private(set) var log = PacketLog()

    private var central: CBCentralManager?
    private var peripheral: CBPeripheral?
    private var writeCharacteristic: CBCharacteristic?
    private var wantsScan = false
    private var scanTimeout: DispatchWorkItem?

    var isConnected: Bool {
        writeCharacteristic != nil && peripheral?.state == .connected
    }

    var isBusy: Bool {
        switch status {
        case .waitingForBluetooth, .scanning, .connecting, .connected: return true
        case .off, .problem: return false
        }
    }

    /// Starts scanning. Only ever called from the Connect button.
    func connect() {
        wantsScan = true
        if let central {
            if central.state == .poweredOn { startScan() } else { handle(state: central.state) }
        } else {
            status = .waitingForBluetooth
            central = CBCentralManager(delegate: self, queue: nil)
        }
    }

    func disconnect() {
        wantsScan = false
        cancelScanTimeout()
        central?.stopScan()
        if let peripheral { central?.cancelPeripheralConnection(peripheral) }
        peripheral = nil
        writeCharacteristic = nil
        status = .off
    }

    /// Sends a packet if a wristband is connected. Returns true if it was sent.
    @discardableResult
    func send(_ bytes: [UInt8], label: String) -> Bool {
        guard let peripheral, let characteristic = writeCharacteristic, peripheral.state == .connected else {
            return false
        }
        let type: CBCharacteristicWriteType =
            characteristic.properties.contains(.writeWithoutResponse) ? .withoutResponse : .withResponse
        peripheral.writeValue(Data(bytes), for: characteristic, type: type)
        log.append(bytes, label: label)
        return true
    }

    func clearLog() {
        log.clear()
    }

    // MARK: - Private

    private func startScan() {
        guard let central, wantsScan, peripheral == nil else { return }
        status = .scanning
        // Scan without a service filter so devices that only advertise a
        // name (some Bangle.js and micro:bit builds) are still found.
        central.scanForPeripherals(withServices: nil, options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
        cancelScanTimeout()
        let timeout = DispatchWorkItem { [weak self] in
            guard let self, self.status == .scanning else { return }
            self.central?.stopScan()
            self.wantsScan = false
            self.status = .problem("No wristband found. Check it is switched on and close by, then tap Connect again.")
        }
        scanTimeout = timeout
        DispatchQueue.main.asyncAfter(deadline: .now() + Self.scanTimeoutSeconds, execute: timeout)
    }

    private func cancelScanTimeout() {
        scanTimeout?.cancel()
        scanTimeout = nil
    }

    private func handle(state: CBManagerState) {
        switch state {
        case .poweredOn:
            if wantsScan { startScan() }
        case .poweredOff:
            status = .problem("Bluetooth is switched off on this iPhone. Turn it on, then tap Connect again.")
        case .unauthorized:
            status = .problem("OpenHear Haptics is not allowed to use Bluetooth. You can allow it in the iPhone Settings app.")
        case .unsupported:
            status = .problem("This device does not support Bluetooth Low Energy.")
        case .resetting, .unknown:
            status = .waitingForBluetooth
        @unknown default:
            status = .waitingForBluetooth
        }
    }

    private func fail(_ message: String) {
        if let peripheral { central?.cancelPeripheralConnection(peripheral) }
        peripheral = nil
        writeCharacteristic = nil
        wantsScan = false
        status = .problem(message)
    }

    static func matches(name: String?, advertisedServices: [CBUUID]) -> Bool {
        if advertisedServices.contains(uartService) { return true }
        guard let name else { return false }
        return namePrefixes.contains { name.hasPrefix($0) }
    }
}

extension WristbandBluetooth: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        handle(state: central.state)
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        guard self.peripheral == nil else { return }
        let name = (advertisementData[CBAdvertisementDataLocalNameKey] as? String) ?? peripheral.name
        let services = advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID] ?? []
        guard Self.matches(name: name, advertisedServices: services) else { return }
        central.stopScan()
        cancelScanTimeout()
        self.peripheral = peripheral
        peripheral.delegate = self
        status = .connecting(name ?? "wristband")
        central.connect(peripheral)
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        peripheral.discoverServices([Self.uartService])
    }

    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        fail("Could not connect to the wristband. Tap Connect to try again.")
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        guard peripheral == self.peripheral else { return }
        self.peripheral = nil
        writeCharacteristic = nil
        wantsScan = false
        status = error == nil ? .off : .problem("The wristband disconnected. Tap Connect to try again.")
    }
}

extension WristbandBluetooth: CBPeripheralDelegate {
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let service = peripheral.services?.first(where: { $0.uuid == Self.uartService }) else {
            fail("Connected, but the device has no UART service, so it cannot take OpenHear packets.")
            return
        }
        peripheral.discoverCharacteristics(nil, for: service)
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        let writable = (service.characteristics ?? []).filter {
            $0.properties.contains(.write) || $0.properties.contains(.writeWithoutResponse)
        }
        guard let chosen = writable.first(where: { $0.uuid == Self.preferredWriteCharacteristic }) ?? writable.first else {
            fail("Connected, but the device has nothing OpenHear can write to.")
            return
        }
        writeCharacteristic = chosen
        status = .connected(peripheral.name ?? "wristband")
    }
}
