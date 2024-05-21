import pytest
import json
import decoder
import sys


@pytest.fixture
def format_strings():
    return {
        '1077736': '%s: debug string',
        '1077756': 'error string',
        '1078980': 'Debug',
        '1079004': 'EIP: 0x%08x',
        '1080899': ''
    }


@pytest.fixture
def binary_path(tmp_path):
    binary_file = tmp_path / "test_binary.bin"
    binary_file.write_bytes(b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a')
    return str(binary_file)


@pytest.fixture
def json_path(tmp_path, format_strings):
    json_file = tmp_path / "test_json.json"
    with open(json_file, 'w') as f:
        json.dump(format_strings, f)
    return str(json_file)


# Проверяет, что форматированные строки правильно читаются из JSON
def test_read_json_format_strings(json_path):
    expected_format_strings = {
        '1077736': '%s: debug string',
        '1077756': 'error string',
        '1078980': 'Debug',
        '1079004': 'EIP: 0x%08x',
        '1080899': ''
    }
    result = decoder.read_json_format_strings(json_path)
    assert result == expected_format_strings


# Проверяет правильность вычисления CRC8
def test_crc8_check():
    data = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a'
    expected_crc8 = 164
    assert decoder.crc8_check(data) == expected_crc8


# Проверяет правильность разбора аргументов
def test_parse_arguments(format_strings):
    format_string = '%s %d %x'
    data = b'\x05\x00\x00\x00'
    expected_arguments = ['<unknown string at 5>']
    assert decoder.parse_arguments(format_string, data, format_strings) == expected_arguments


def test_parse_binary_log_file(binary_path, json_path, capsys):
    format_strings = decoder.read_json_format_strings(json_path)
    decoder.parse_binary_log_file(binary_path, format_strings)
    captured = capsys.readouterr()

    # Проверка ожидаемых выводов
    assert "Processing page 0\n" in captured.err
    assert "SyncFrame - CRC8: 1, Expected CRC8: 14, Size: 2, StringAddr: 100992003, Timestamp: 168364039" in captured.err


def test_main(capsys, binary_path, json_path):
    # Сохраняем оригинальные аргументы
    original_argv = sys.argv
    # Устанавливаем новые аргументы для теста
    sys.argv = ["decoder.py", binary_path, "-m", json_path]

    try:
        decoder.main()
    finally:
        sys.argv = original_argv

    captured = capsys.readouterr()

    # Возвращаем оригинальные аргументы
    sys.argv = original_argv

    assert "Binary file" in captured.err
    assert "JSON file" in captured.err