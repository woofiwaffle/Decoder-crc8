import unittest
import decoder
import os
import tempfile
import json
import struct

class TestDecoder(unittest.TestCase):

    def test_crc8_check(self):
        data = b"Hello, World!"
        expected_crc8 = 135  # ожидаемое значение
        self.assertEqual(decoder.crc8_check(data), expected_crc8)

    def test_parse_arguments(self):
        format_string = "%s %d %x"
        data = struct.pack('III', 1, 7, 10)  # Пример данных
        format_strings = {
            "1": "world"
        }
        expected_arguments = ["world", 7, 10]
        self.assertEqual(decoder.parse_arguments(format_string, data, format_strings), expected_arguments)

    def test_read_json_format_strings(self):
        # Создаем временный JSON файл с тестовыми данными
        test_data = {
            "20185088": "%s %s initialized!",
            "20185092": "<inf>",
            "20185096": "QSPI",
            "20185100": "%s %s:  FLASH_Init",
            "20185104": "flash",
            "20185108": "%s %s:  Header loaded. Partitions table offset: 0x%04X",
            "20185112": "%s %s:  Partition table loaded",
            "20185116": "%s %s:  History length %d, last flag at %04X.",
            "20185120": "bf"
        }
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp_file:
            json.dump(test_data, tmp_file)
            tmp_file_path = tmp_file.name

        expected_format_strings = test_data
        self.assertEqual(decoder.read_json_format_strings(tmp_file_path), expected_format_strings)

        os.remove(tmp_file_path)  # Удаляем временный файл после теста

    def test_read_binary_file(self):
        # Создаем временный бинарный файл с тестовыми данными
        test_data = b'\x01\x02\x03\x04'
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_data)
            tmp_file_path = tmp_file.name

        with open(tmp_file_path, 'rb') as f:
            data = f.read()
            self.assertEqual(data, test_data)

        os.remove(tmp_file_path)  # Удаляем временный файл после теста

    def test_crc8_check_invalid_data(self):
        data = b"Invalid data"
        expected_crc8 = 0  # Пример ожидаемого значения для некорректных данных
        self.assertNotEqual(decoder.crc8_check(data), expected_crc8)

    def test_parse_arguments_invalid_format(self):
        format_string = "%s %d %x"
        data = struct.pack('III', 1, 7, 10)  # Пример данных
        format_strings = {
            "2": "not_found"
        }
        expected_arguments = ['<unknown string at 1>', 7, 10]
        self.assertEqual(decoder.parse_arguments(format_string, data, format_strings), expected_arguments)

if __name__ == "__main__":
    unittest.main()