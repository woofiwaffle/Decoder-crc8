# python decoder.py -m input.json input.bin
import json
import struct
import sys
import argparse


def read_json_format_strings(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)


# функция для вычисления crc8
def crc8(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


# функция парсинга для бинарного кода
def parse_binary_log_file(binary_path, format_strings):
    with open(binary_path, 'rb') as f:
        page_size = 512
        page_number = 0
        while True:
            page = f.read(page_size)
            if not page:
                break
            print(f"Processing page {page_number}", file=sys.stderr)
            try:
                parse_page(page, format_strings)
            except Exception as e:
                print(f"Error parsing page {page_number}: {e}", file=sys.stderr)
            page_number += 1


# функция для парсинга бинарного файла журнала
def parse_page(page, format_strings):
    offset = 0
    page_size = len(page)
    last_timestamp = 0

    while offset < page_size:
        try:
            if page_size - offset < 10:
                # print(f"No enough data for SyncFrame at offset {offset}", file=sys.stderr)
                break

            crc8_value, size, string_addr, timestamp = struct.unpack_from('<BBII', page, offset)
            expected_crc8 = crc8(page[offset + 1:offset + size])
            print(
                f"SyncFrame - CRC8: {crc8_value}, Expected CRC8: {expected_crc8}, Size: {size}, StringAddr: {string_addr}, Timestamp: {timestamp}",
                file=sys.stderr)

            if string_addr != 0 or expected_crc8 != crc8_value:
                # print(f"Invalid SyncFrame at offset {offset}", file=sys.stderr)
                # offset += size
                # continue
                break

            offset += size
            last_timestamp = timestamp

            while offset < page_size:
                if page_size - offset < 10:
                    # print(f"No enough data for Message at offset {offset}", file=sys.stderr)
                    break

                crc8_value, size, string_addr, time_offset_us = struct.unpack_from('<BBII', page, offset)
                expected_crc8 = crc8(page[offset + 1:offset + size])
                print(
                    f"Message - CRC8: {crc8_value}, Expected CRC8: {expected_crc8}, Size: {size}, "
                    f"StringAddr: {string_addr}, "
                    f"TimeOffsetUs: {time_offset_us}",
                    file=sys.stderr)

                if expected_crc8 != crc8_value:
                    print(f"Invalid Message at offset {offset}", file=sys.stderr)
                    offset += size
                    continue

                data = page[offset + 10:offset + size]
                if str(string_addr) in format_strings:
                    format_string = format_strings[str(string_addr)]
                    print_log_message(last_timestamp, time_offset_us, format_string, data)
                else:
                    print(f"Unknown format string address {string_addr} at offset {offset}", file=sys.stderr)

                offset += size
        except Exception as e:
            # print(f"Error processing data at offset {offset}: {e}", file=sys.stderr)
            # Move to the next SyncFrame or break if no more data
            while offset < page_size:
                if page[offset] == 0:  # SyncFrame
                    offset += 10
                    break
                offset += 1


def print_log_message(timestamp, time_offset_us, format_string, data):
    timestamp_str = f"{timestamp:010}.{time_offset_us:06}"
    try:
        arguments = parse_arguments(format_string, data)
        log_message = format_string % tuple(arguments)
    except TypeError as e:
        log_message = format_string % tuple(f"%{fmt}" for fmt in format_string.split('%')[1:])
        print(f"Error formatting log message: {e}", file=sys.stderr)

    print(f"{timestamp_str} {log_message}")


def parse_arguments(format_string, data):
    specifiers = {
        'c': 'b',
        'd': 'i',
        'u': 'I',
        'x': 'I',
        'X': 'I',
        's': 'I',
        'lld': 'q',
        'llu': 'Q'
    }

    args = []
    data_offset = 0
    format_parts = format_string.split('%')[1:]
    for part in format_parts:
        specifier = part.strip("0123456789._")
        if specifier in specifiers:
            fmt = specifiers[specifier]
            size = struct.calcsize(fmt)
            if data_offset + size > len(data):
                print(f"Not enough data for format specifier {specifier} in format string '{format_string}'",
                     file=sys.stderr)
                break
            value = struct.unpack_from(fmt, data, data_offset)[0]
            if specifier == 's':
                value = value.to_bytes(4, 'little').decode('utf-8')
            elif specifier == 'X':
                value = f"{value:08X}"
            elif specifier == 'u':
                value = str(value)
            args.append(value)
            data_offset += size
        else:
            print(f"Unknown format specifier {specifier} in format string '{format_string}'", file=sys.stderr)
            args.append(f"%{specifier}")

    return args

def main():
    parser = argparse.ArgumentParser(description='Decode binary log file.')
    parser.add_argument('binary_file', help='Path to the binary log file.')
    parser.add_argument('-m', '--json_file', required=True, help='Path to the JSON format strings file.')

    args = parser.parse_args()

    print(f"Binary file: {args.binary_file}", file=sys.stderr)
    print(f"JSON file: {args.json_file}", file=sys.stderr)

    try:
        format_strings = read_json_format_strings(args.json_file)
        parse_binary_log_file(args.binary_file, format_strings)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
