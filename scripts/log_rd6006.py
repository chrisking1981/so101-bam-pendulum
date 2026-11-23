"""Record RD6006 output telemetry without writing any Modbus registers."""
import argparse
import json
import struct
import time

import serial


def crc16(data):
    value = 0xffff
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xa001 if value & 1 else 0)
    return value.to_bytes(2, 'little')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port')
    parser.add_argument('--seconds', type=float, default=10)
    args = parser.parse_args()
    request = bytes((1, 3, 0, 8, 0, 4))
    with serial.Serial(baudrate=115200, timeout=.3, write_timeout=.3) as controller:
        controller.dtr = controller.rts = False
        controller.port = args.port
        controller.open()
        controller.reset_input_buffer()
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            sent = time.monotonic()
            controller.write(request + crc16(request))
            response = controller.read(13)
            received = time.monotonic()
            reading = {'monotonic_s': (sent + received)/2, 'round_trip_s': received - sent}
            if (len(response) == 13 and response[:3] == bytes((1, 3, 8))
                    and crc16(response[:-2]) == response[-2:]):
                v_set, limit, v_out, i_out = struct.unpack('>4H', response[3:-2])
                reading.update(v_set=v_set/100, i_limit=limit/1000, v_out=v_out/100, i_out=i_out/1000)
            else:
                reading['error'] = 'invalid Modbus response'
                controller.reset_input_buffer()
            print(json.dumps(reading), flush=True)
            time.sleep(.025)


if __name__ == '__main__':
    main()
