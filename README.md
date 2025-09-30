# LichessPgnParser

A Python parser designed to efficiently process large PGN (Portable Game Notation) files from the [Lichess open database](https://database.lichess.org/).

## Features

- **Memory Efficient**: Processes files in configurable chunks using a generator pattern, enabling parsing of multi-gigabyte databases without loading entire files into memory
- **Error Handling**: Comprehensive logging system with multiple verbosity levels and detailed error reporting
- **Type Safety**: Strongly typed with Python type annotations and automatic type conversion
- **Flexible Configuration**: Adjustable buffer sizes and debug modes to suit different use cases

## Installation
Clone this repository:

```bash
git clone https://github.com/sciacnoghi/LichessPgnParser.git
cd LichessPgnParser
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)

## Usage

### Basic Example

```python

# Initialize the parser
parser = PgnParser(
    file_name="Pgn/lichess_db_standard_rated_2013-01.pgn",
    buffer_size=200_000,
    debug_mode=DebugMode.VERBOSE
)

# Iterate through games
for game in parser.parse_games():
    print(f"White: {game.white} vs Black: {game.black}")
    print(f"Result: {game.result}")
    print(f"Opening: {game.opening}")
    print("---")
```

### Debug Modes

The parser supports three debug modes:

- **`DebugMode.SILENT`**: Logs only errors to file
- **`DebugMode.VERBOSE`**: Logs info and errors to both console and file
- **`DebugMode.DEBUG`**: Logs detailed debug information to both console and file

```python
# Silent mode
parser = PgnParser("games.pgn", debug_mode=DebugMode.SILENT)

# Debug mode
parser = PgnParser("games.pgn", debug_mode=DebugMode.DEBUG)
```

### Adjusting Buffer Size

For very large files, you may want to increase the buffer size:

```python
# Process 1MB chunks at a time
parser = PgnParser("large_database.pgn", buffer_size=1_000_000)
```

## ChessGame Object

Each parsed game is returned as a `ChessGame` object with the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `event` | str | Tournament or match event |
| `site` | str | Location (URL for online games) |
| `white` | str | White player username |
| `black` | str | Black player username |
| `result` | str | Game result (1-0, 0-1, or 1/2-1/2) |
| `utcdate` | datetime | Game date |
| `utctime` | time | Game start time |
| `whiteelo` | int | White player rating |
| `blackelo` | int | Black player rating |
| `eco` | str | ECO opening code |
| `opening` | str | Opening name |
| `timecontrol` | str | Time control format |
| `termination` | str | How the game ended |
| `moves` | str | Complete move sequence |

## File Structure

```
LichessPgnParser/
├── main.py           # Main parser implementation
├── Pgn/              # Directory for PGN files
└── Logs/             # Generated log files (created automatically)
```

## How It Works

1. **Chunked Reading**: The parser reads the PGN file in configurable chunks to manage memory efficiently
2. **Pattern Matching**: Uses regex to identify complete game records within chunks
3. **Leftover Handling**: Maintains partial games between chunks to ensure no data is lost
4. **Type Conversion**: Automatically converts string values to appropriate types (datetime, int, etc.)
5. **Validation**: Validates each game's structure and logs errors for malformed data

## Error Handling

The parser implements robust error handling:

- Invalid games are logged but don't interrupt processing
- Malformed headers are caught and reported with line numbers
- Type conversion errors are handled gracefully
- Logs are saved to `Logs/PgnParser.log`

## Performance Considerations

- **Buffer Size**: Larger buffers (200KB-1MB) improve performance but use more memory
- **Generator Pattern**: Games are yielded one at a time, allowing processing to begin immediately
- **Regex Optimization**: Compiled pattern matching ensures fast game extraction

## Limitations

- Designed specifically for Lichess database format
- May not support all PGN format variations from other sources
- Requires complete game records (cannot parse mid-game positions)

## Acknowledgments
- Built for parsing data from [Lichess Open Database](https://database.lichess.org/)
- PGN format specification: [Standard: Portable Game Notation](https://www.chessclub.com/help/PGN-spec)
