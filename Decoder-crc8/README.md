# Test DAASDE

## Input data

- A JSON file with a set of format strings;
- A binary file with a log messages dump.


### The Task

Develop a script `decoder.py` that decodes and prints log messages from the binary file to `stdout`. Keep message output order the same as in the binary file.
The script messages (errors, etc.) should be printed to `stderr`.

The script must take one positional argument "path to the binary file" and at least one named argument (`-m`) "path to the JSON file".


### JSON file data format

The JSON file contains a collection of values `"<address>": "<format string>"`, where:
- `"<address>"` is a non-zero address of the format string in program memory (numeric string identifier);
- `"<string>"` is a valid format string for the C `printf` function.

Example:
```
{
    "1077736": "%s: debug string",
    "1077756": "error string",
    "1078980": "Debug",
    "1079004": "EIP: 0x%08x",
    "1080899": ""
}
```

Format strings support a limited set of format specifiers `%c`, `%s`, `%d`, `%u`, `%llu`, `%lld`, `%x`, `%X`, a `0` flag, and a numeric alignment value.
Examples of valid specifiers: `%c`, `%2d`, `%lld`, `%02X`.


### Binary file data format

The binary file consists of `pages` each 512 bytes in size, byte order `LE`. The binary file size is a multiple of the `page` size.

Each `page` starts with a `SyncFrame` structure:
```
struct SyncFrame {
    uint8_t  crc8;          // Checksum of all fields of the structure (except for the crc8 field)
    uint8_t  size;          // Size of the SyncFrame structure in bytes
    uint32_t stringAddr;    // Has a 0 value. It's guaranteed that in the SyncFrame structure this value is always 0
    uint32_t timestamp;     // Some unix time value for all next log messages
}
```

The `SyncFrame` structure can be written not only at the beginning, but also anywhere on `page` with a different (new) `timestamp` value.

After structure `SyncFrame`, each page contains from 0 to N packed `Message` structures:
```
struct Message {
    uint8_t  crc8;          // Checksum of all fields of the structure (except for the crc8 field)
    uint8_t  size;          // Size of the Message structure in bytes
    uint32_t stringAddr;    // Address of the format string in program memory (its numeric identifier)
    uint32_t timeOffsetUs;  // Message offset in microseconds from the timestamp value in previous SyncFrame structure (value range [0;999999])
    uint8_t  data[size-10]; // Packed argument values for the format string specified in stringAddr field
}
```

The number of bytes allocated for storing arguments in the `data` array depends on the corresponding format specifier in the format string:

| Format Specifier             | Argument size |
|------------------------------|---------------|
| `%c`                         | 1 byte        |
| `%s`, `%d`, `%u`, `%x`, `%X` | 4 bytes       |
| `%lld`, `%llu`               | 8 bytes       |

For `%s` format specifiers, in `data` is stored the 32-bit address of the string (numeric identifier).


### Extra requirements

Before each log message, print its `timestamp` and `timeOffsetUs` values in format `%010u.%06u`, separated from the log message by a space.

If the number of arguments in log message doesn't match the corresponding format string, the extra arguments are ignored, and their specifier is printed in the format string instead of missing arguments.

Example:
```
Format string: "Test string: %s, size: %d"
Message args: ["Hello"]
Output string: "Test string: Hello, size: %d"
```

If an invalid `SyncFrame` or `Message` structure is found, the structure and remaining `page` data should be skipped.
