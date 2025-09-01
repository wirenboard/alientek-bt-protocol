import binascii
import socket
import struct
from binascii import hexlify, unhexlify


def to_bytes(s):
    return unhexlify(s.replace(' ', ''))

def add_crc(data):
    crc = 256 - sum(data) % 256
    return data + struct.pack('B', crc)

def decode_packet_bytes(packet: bytes) -> dict:
    """
    Decode a binary packet (17 bytes) into a value and two raw 16-bit fields.

    Args:
        packet (bytes): A 17-byte binary message.

    Returns:
        dict: {
            'value': float,         # decoded final value
            'raw1': int,            # raw value 1 (bytes 10–11)
            'raw2': int             # raw value 2 (bytes 12–13)
        }
    """
    if len(packet) < 17:
        raise ValueError("Packet must be at least 17 bytes long.")

    exponent_byte = packet[9]
    # digits = (exponent_byte - 0x10) // 2
    # if digits < 0:
        # raise ValueError(f"Unsupported exponent byte: 0x{exponent_byte:02X}")

    unit = exponent_byte >> 4
    exponent = -((exponent_byte & 0x0F) // 2)
    exponent += unit * 3

    # Mantissa is in bytes 14–15, little-endian
    mantissa = packet[14] + (packet[15] << 8)
    value = mantissa * (10 ** exponent)

    # Raw values (2 x 16-bit), little-endian
    raw1 = packet[10] + (packet[11] << 8)
    raw2 = packet[12] + (packet[13] << 8)

    return {
        'value': value,
        'raw1': raw1,
        'raw2': raw2,
        'mantissa' : mantissa,
        'exp' : hex(exponent_byte),
        'unit': unit
    }



s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
# s.connect(('63:14:06:46:58:85', 1))
s.connect(('F8:42:8A:03:33:0B', 1))

while 1:
    packet = add_crc(to_bytes('af 05 03 09 01'))
    s.send(packet)
    data = s.recv(1024)
    print(binascii.hexlify(packet))
    print(binascii.hexlify(data))
    print((data))
    print(decode_packet_bytes(data))
