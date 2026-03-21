# AutoCyberChef 🔍

> A lightweight command-line toolkit for **automatic encoding detection and decoding** — built for CTF challenges, security analysis, and data processing workflows.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-84%20passed-brightgreen)]()
[![Lines of Code](https://img.shields.io/badge/Code-2000%2B%20lines-orange)]()

---

## ✨ Why AutoCyberChef?

When doing CTF challenges or security analysis, you often face strings like:

```
U0dWc2JIOD0=
```

Is it Base64? Double-encoded? ROT13 inside Hex? Manually peeling each layer wastes time.

AutoCyberChef detects and unwraps encoding layers **automatically** — giving you the answer in seconds instead of minutes.

```
$ python main.py auto U0dWc2JIOD0=

  Layer 1: [Base64]  →  SGVsbG8=
  Layer 2: [Base64]  →  Hello

Final result: Hello
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/norniy/auto-cyberchef.git
cd auto-cyberchef
pip install -r requirements.txt
python main.py shell
```

---

## 📦 Installation

**Requirements:** Python 3.9 or higher. No heavy dependencies — core features use the standard library only.

```bash
# Clone the repository
git clone https://github.com/norniy/auto-cyberchef.git
cd auto-cyberchef

# Install optional dev dependencies (pytest for running tests)
pip install -r requirements.txt

# Verify installation
python main.py --version
```

---

## 🎮 Features

| Feature | Description |
|---|---|
| **Auto-detect** | Identify Base64, Hex, Binary, URL, ROT13, Morse, HTML, Caesar, Base32 |
| **Auto-decode** | Automatically unwrap up to 10 nested encoding layers |
| **Interactive shell** | REPL with command history and tab completion |
| **Batch file decode** | Decode every line of a file in one command |
| **Brute-force mode** | Try every decoder at once and show all results |
| **Confidence scores** | Ranked probability scores for each detected encoding |
| **JSON output** | Machine-readable output for pipeline integration |

---

## 📖 Usage

### Interactive Shell (Recommended)

Launch the interactive shell for a full session:

```bash
python main.py shell
```

```
autochef > decode SGVsbG8=
  Detected: Base64
  Result:   Hello

autochef > detect 48656c6c6f
  Possible encodings:
    - Hex
    - Base64

autochef > auto U0dWc2JIOD0=
  2 layer(s) found:
    Layer 1: [Base64]  →  SGVsbG8=
    Layer 2: [Base64]  →  Hello
  Final: Hello

autochef > brute "Uryyb Jbeyq"
    ✓ ROT13     Hello World
    ✓ Caesar    Hello World

autochef > history
autochef > exit
```

Shell supports ↑/↓ arrow keys for command history on Unix/macOS.

---

### One-shot Commands

#### `decode` — Decode a string

```bash
# Auto-detect encoding and decode
python main.py decode SGVsbG8=

# Force a specific encoding
python main.py decode 48656c6c6f -e hex
python main.py decode "Uryyb Jbeyq" -e rot13
python main.py decode ".... . .-.. .-.. ---" -e morse

# Output as JSON
python main.py decode SGVsbG8= --json
```

**Output:**
```
Detected encoding: Base64
Decoded result: Hello
```

---

#### `detect` — Identify encoding type

```bash
# List possible encodings
python main.py detect SGVsbG8=

# Show confidence scores
python main.py detect SGVsbG8= --confidence
```

**Output:**
```
Possible encodings:
  - Base64

Encoding confidence scores:
  Base64        ████████████████████ 95.0%
```

---

#### `auto` — Multi-layer automatic decode

```bash
# Automatically unwrap all layers
python main.py auto U0dWc2JIOD0=

# Show step-by-step progress
python main.py auto U0dWc2JIOD0= --verbose

# Limit decode depth
python main.py auto U0dWc2JIOD0= --max-layers 5
```

**Output:**
```
Auto-decode: 2 layer(s) found

  Layer 1: [Base64]  →  SGVsbG8=
  Layer 2: [Base64]  →  Hello

Final result: Hello
```

---

#### `decode-file` — Batch decode a file

```bash
# Decode each line of a file
python main.py decode-file encoded.txt

# Save output to a file
python main.py decode-file encoded.txt -o decoded.txt

# Show layer-by-layer details
python main.py decode-file encoded.txt --layers

# Force a specific encoding for all lines
python main.py decode-file encoded.txt -e base64

# Output as JSON
python main.py decode-file encoded.txt --json

# Treat entire file as one string
python main.py decode-file encoded.txt --blob
```

Example input file (`encoded.txt`):
```
SGVsbG8=
48656c6c6f
.... . .-.. .-.. ---
```

Output:
```
Hello
Hello
HELLO

Processed 3 line(s): 3 decoded, 0 failed
```

---

#### `brute` — Try all decoders

```bash
# Try every decoder
python main.py brute SGVsbG8=

# Also show failed attempts
python main.py brute SGVsbG8= --show-failures

# Include all 25 Caesar cipher shifts
python main.py brute "Khoor" --caesar
```

---

#### `stats` — File encoding statistics

```bash
python main.py stats encoded.txt
```

**Output:**
```
File statistics: encoded.txt
  Total lines:   10
  Decoded lines: 9
  Failed lines:  1

Encoding breakdown:
  Base64         6
  Hex            3
```

---

## 🔤 Supported Encodings

| Encoding | Example Input | Decoded Output |
|---|---|---|
| Base64 | `SGVsbG8=` | `Hello` |
| Base32 | `JBSWY3DP` | `Hello` |
| Hexadecimal | `48656c6c6f` | `Hello` |
| Binary | `01001000 01100101...` | `Hello` |
| URL Encoding | `Hello%20World%21` | `Hello World!` |
| HTML Entities | `&#72;&#101;&#108;...` | `Hello` |
| ROT13 | `Uryyb` | `Hello` |
| Morse Code | `.... . .-.. .-.. ---` | `HELLO` |
| Caesar Cipher | `Khoor` (shift 3) | `Hello` |

---

## 🏗️ Project Structure

```
auto-cyberchef/
│
├── autochef/
│   ├── __init__.py       # Package entry point and public API
│   ├── detector.py       # Encoding detection (regex + heuristics + confidence scoring)
│   ├── decoder.py        # Individual decode implementations for all formats
│   ├── pipeline.py       # Multi-layer auto-decode orchestration
│   ├── file_handler.py   # Batch file processing and JSON output
│   └── utils.py          # Shared helpers (entropy, printability, string analysis)
│
├── tests/
│   └── test_basic.py     # 84 unit tests covering all modules
│
├── main.py               # CLI entry point (argparse + interactive shell)
├── requirements.txt
└── README.md
```

---

## 🔌 Use as a Python Library

AutoCyberChef can be imported directly into your own scripts:

```python
from autochef.detector import detect_encoding, get_encoding_confidence
from autochef.decoder import decode_base64, decode_hex, decode_by_name
from autochef.pipeline import auto_decode

# Detect encodings
encodings = detect_encoding("SGVsbG8=")
print(encodings)  # ['Base64']

# Get confidence scores
scores = get_encoding_confidence("SGVsbG8=")
print(scores)  # {'Base64': 0.95}

# Decode a specific format
result, success = decode_base64("SGVsbG8=")
print(result)  # Hello

# Decode by name
result, success = decode_by_name("hex", "48656c6c6f")
print(result)  # Hello

# Auto multi-layer decode
steps, final = auto_decode("U0dWc2JIOD0=")
print(final)  # Hello
for encoding, before, after in steps:
    print(f"{encoding}: {before} -> {after}")
```

---

## 🧪 Running Tests

```bash
# Run all 84 tests
python -m unittest tests.test_basic -v

# Run a specific test class
python -m unittest tests.test_basic.TestPipeline -v

# Run with pytest (if installed)
pytest tests/ -v
```

---

## 🤝 Contributing

Contributions are welcome! Here are some ways to get started:

- 🐛 **Report bugs** by opening an [Issue](https://github.com/norniy/auto-cyberchef/issues)
- ✨ **Request features** via Issues tagged `enhancement`
- 🔧 **Fix a bug or add a feature** — open a Pull Request

### Good First Issues

Look for issues tagged [`good first issue`](https://github.com/norniy/auto-cyberchef/issues?q=label%3A%22good+first+issue%22):

- Add support for a new encoding (Base58, XOR, etc.)
- Add more test cases
- Improve README translations
- Fix a typo or documentation gap

### Development Setup

```bash
git clone https://github.com/norniy/auto-cyberchef.git
cd auto-cyberchef
pip install -r requirements.txt
python -m unittest tests.test_basic -v   # make sure all tests pass before contributing
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🔗 Related Projects

- [CyberChef](https://github.com/gchq/CyberChef) — The original web-based "Cyber Swiss Army Knife"
- [Ciphey](https://github.com/Ciphey/Ciphey) — AI-powered automatic decryption tool

AutoCyberChef is different: **no browser required, no heavy ML dependencies** — just Python 3.9+ and the standard library.

---

<p align="center">
  Made for CTF players, security researchers, and anyone who spends too long manually decoding strings.
  <br>
  If this tool saved you time, consider giving it a ⭐
</p>
