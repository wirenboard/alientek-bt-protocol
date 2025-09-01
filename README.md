# Alientek Device Protocol Documentation

This repository contains protocol documentation and implementation for two Alientek devices:
- **EL15 Electronic Load**
- **DM40 Multimeter**

Both devices communicate via Bluetooth RFCOMM protocol.

## Connection Setup

1. Create Bluetooth RFCOMM socket
2. Connect to device MAC address on channel 1
3. Send commands and receive responses

## Packet Structure

### Common Elements

All packets use the following structure:
- **Header**: Device-specific identifier
- **Command/Data**: Variable length payload
- **CRC**: Single byte checksum

### CRC Calculation

The CRC is calculated as: `256 - sum(all_data_bytes) % 256`

## DM40 Multimeter Protocol

### Connection
- **MAC Address**: `63:14:06:46:58:85` or `F8:42:8A:03:33:0B`
- **Channel**: 1

### Command Format
```
AF 05 03 09 01 [CRC]
```

### Response Format (17 bytes)
```
Byte    Description
0-8     Header/Status
9       Exponent byte (unit and decimal places)
10-11   Raw value 1 (little-endian)
12-13   Raw value 2 (little-endian)
14-15   Mantissa (little-endian)
16      CRC
```

### Value Decoding Algorithm
1. Extract exponent byte (byte 9)
2. Calculate unit: `exponent_byte >> 4`
3. Calculate exponent: `-(exponent_byte & 0x0F) // 2 + unit * 3`
4. Extract mantissa from bytes 14-15 (little-endian)
5. Final value: `mantissa * 10^exponent`

## EL15 Electronic Load Protocol

### Connection
- **MAC Address**: `F8:42:8A:03:33:0B`
- **Channel**: 1

### Command Format
```
AF 07 03 [CMD] [DATA...] [CRC]
```

### Commands

#### Query Status
- Command: `AF 07 03 08 00 [CRC]`
- Returns current device status (28 bytes)

#### Lock/Unlock Control
- Unlock: `AF 07 03 09 01 00 [CRC]`
- Lock: `AF 07 03 09 01 01 [CRC]`

#### Load Control
- Load Off: `AF 07 03 09 01 00 [CRC]`
- Load On: `AF 07 03 09 01 04 [CRC]`

#### Set Current
- Command: `AF 07 03 04 04 [4-byte float] [CRC]`
- Float is IEEE 754 single precision, little-endian
- Example: 1.0A = `00 00 80 3F`
- Example: 1.234A = `B6 F3 9D 3F`

#### Set Operating Mode
- CC (Constant Current): `AF 07 03 03 01 01 [CRC]`
- Battery CAP: `AF 07 03 03 01 02 [CRC]`
- CV (Constant Voltage): `AF 07 03 03 01 09 [CRC]`
- Battery DCR: `AF 07 03 03 01 0A [CRC]`
- CR (Constant Resistance): `AF 07 03 03 01 11 [CRC]`
- CP (Constant Power): `AF 07 03 03 01 19 [CRC]`

#### Device Management
- Discovery: `AF FF FF 00 00 [CRC]`
  - Response: `DF FF FF 00 02 07 03 [CRC]`
- Get Device Name: `AF 07 03 07 00 [CRC]`
  - Response: `DF 07 03 07 0A "EL15" + 6 null bytes [CRC]`
- Set Device Name: `AF 07 03 06 0A [10-byte name] [CRC]`
  - Name is padded with null bytes to 10 bytes total

### Response Format (28 bytes)

```
Example response:
DF 07 03 08 16 41 02 B8 4A 66 41 2A 15 9E 3F 6B 00 00 00 88 80 23 42 7B 14 9E 3F AD
0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
<-header->           <--volt --> <-current-> <--time---> <-temp--->   <---setp-> CRC

Byte    Description
0-6     Header (DF 07 03 08 unk1 mode/fan run)
7-10    Voltage (float, little-endian)
11-14   Current (float, little-endian)  
15-18   Runtime (long, little-endian)
19-22   Temperature (float, little-endian)
23-26   Setpoint (float, little-endian)
27      CRC
```

#### Status Byte Details
- **Byte 4**: Unknown parameter
- **Byte 5**: Lower 4 bits = Mode, Upper 4 bits = Fan status
- **Byte 6**: Run status

### Value Decoding Algorithm
1. Extract voltage from bytes 7-10 (IEEE 754 float, little-endian)
2. Extract current from bytes 11-14 (IEEE 754 float, little-endian)
3. Extract runtime from bytes 15-18 (32-bit signed integer, little-endian)
4. Extract temperature from bytes 19-22 (IEEE 754 float, little-endian)
5. Extract setpoint from bytes 23-26 (IEEE 754 float, little-endian)
6. Parse status bytes for mode, fan, and run state

## Usage Examples

### DM40 - Read Measurement
```
PSEUDOCODE:
1. Send measurement request: AF 05 03 09 01 + CRC
2. Receive 17-byte response
3. Decode using DM40 algorithm
4. Display measured value
```

### EL15 - Complete Control Sequence
```
PSEUDOCODE:
1. Connect to device via Bluetooth
2. Send unlock command: AF 07 03 09 01 00 + CRC (??)
3. Set mode to CC: AF 07 03 03 01 01 + CRC
4. Set current setpoint: AF 07 03 04 04 + float_bytes + CRC
5. Enable load: AF 07 03 09 01 04 + CRC
6. Query status: AF 07 03 08 00 + CRC
7. Decode 28-byte response for current readings
8. Display voltage, current, mode, and runtime
```

## Mode Values

| Mode | Value | Description |
|------|--------|-------------|
| CC   | 0x01   | Constant Current |
| CAP  | 0x02   | Battery Capacity Test |
| CV   | 0x09   | Constant Voltage |
| DCR  | 0x0A   | Battery DCR Test |
| CR   | 0x11   | Constant Resistance |
| CP   | 0x19   | Constant Power |

## Protocol Notes

- All multi-byte values use little-endian byte order
- Float values are IEEE 754 single precision (4 bytes)
- CRC is calculated as `256 - sum(data) % 256`
- Always wait for response before sending next command
- Device discovery triggers AT+CBN Bluetooth command on host
- String values are null-padded to fixed lengths
- Runtime is measured in seconds as a 32-bit signed integer
