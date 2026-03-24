"""
main.py - CLI entry point for AutoCyberChef.

Usage:
    python main.py <command> [options] <input>

Commands:
    decode       Decode a string using a specific or auto-detected encoding
    detect       Detect possible encodings in a string
    auto         Automatically decode nested/multi-layer encodings
    decode-file  Batch decode every line of a file
    brute        Try all decoders and show all outputs
    stats        Show encoding statistics for a file

Run `python main.py <command> --help` for per-command options.
"""

import sys
import argparse
import json
from typing import Optional

# Ensure package is importable when run from project root
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autochef.detector import detect_encoding, get_encoding_confidence
from autochef.decoder import decode_by_name, decode_caesar_all
from autochef.pipeline import auto_decode, format_pipeline_output, try_all_decoders
from autochef.file_handler import decode_file, decode_file_blob, decode_file_json, file_stats
from autochef.utils import format_detect_results, format_confidence_results


# ---------------------------------------------------------------------------
# Colour helpers (graceful degradation on Windows without colorama)
# ---------------------------------------------------------------------------

def _colour(text: str, code: str) -> str:
    """Wrap `text` in an ANSI colour code if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(t):  return _colour(t, "32")
def yellow(t): return _colour(t, "33")
def cyan(t):   return _colour(t, "36")
def bold(t):   return _colour(t, "1")
def red(t):    return _colour(t, "31")


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_detect(args: argparse.Namespace) -> int:
    """Handle the `detect` sub-command."""
    data = args.input
    if args.confidence:
        scores = get_encoding_confidence(data)
        print(bold("Encoding confidence scores:"))
        if not scores:
            print(red("  No recognizable encoding detected."))
        else:
            for enc, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                bar_len = int(score * 20)
                bar = '█' * bar_len + '░' * (20 - bar_len)
                print(f"  {cyan(enc):<22} {bar} {score * 100:.1f}%")
    else:
        encodings = detect_encoding(data)
        print(bold("Possible encodings:"))
        if not encodings:
            print(red("  No recognizable encoding detected."))
        else:
            for enc in encodings:
                print(f"  - {cyan(enc)}")
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    """Handle the `decode` sub-command."""
    data = args.input

    if args.encoding:
        enc = args.encoding
        result, success = decode_by_name(enc, data)
        if success:
            print(bold(f"Decoded [{enc}]:"))
            print(green(result))
        else:
            print(red(f"Failed to decode as {enc}: {result}"))
            return 1
    else:
        # Auto-detect best encoding for single-layer decode
        encodings = detect_encoding(data)
        if not encodings:
            print(red("No recognizable encoding detected."))
            return 1
        chosen = encodings[0]
        result, success = decode_by_name(chosen, data)
        if success:
            print(bold(f"Detected encoding: {cyan(chosen)}"))
            print(bold("Decoded result:"), green(result))
        else:
            print(red(f"Detected {chosen} but decode failed: {result}"))
            return 1

    if args.json:
        payload = {
            "input":    data,
            "encoding": args.encoding or (encodings[0] if encodings else None),
            "result":   result,
            "success":  success,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0


def cmd_auto(args: argparse.Namespace) -> int:
    """Handle the `auto` sub-command."""
    data = args.input
    steps, final = auto_decode(data, max_layers=args.max_layers, verbose=args.verbose)

    if not steps:
        print(yellow("No encodings detected. Input may already be plaintext."))
        print(f"Input: {data}")
        return 0

    print(bold(f"Auto-decode: {len(steps)} layer(s) found"))
    print()

    for i, (encoding, before, after) in enumerate(steps, start=1):
        trunc = after if len(after) <= 70 else after[:67] + "..."
        print(f"  {bold(f'Layer {i}:')} [{cyan(encoding)}]  →  {trunc}")

    print()
    print(bold("Final result:"), green(final))

    if args.json:
        payload = {
            "input": data,
            "layers": [
                {"layer": i + 1, "encoding": s[0], "input": s[1], "output": s[2]}
                for i, s in enumerate(steps)
            ],
            "final": final,
        }
        print()
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0


def cmd_decode_file(args: argparse.Namespace) -> int:
    """Handle the `decode-file` sub-command."""
    try:
        if args.blob:
            decode_file_blob(
                args.file,
                output_path=args.output,
                show_layers=args.layers,
            )
        elif args.json:
            decode_file_json(
                args.file,
                output_path=args.output,
                encoding_hint=args.encoding,
            )
        else:
            results = decode_file(
                args.file,
                output_path=args.output,
                show_layers=args.layers,
                encoding_hint=args.encoding,
                skip_errors=True,
            )
            succeeded = sum(1 for r in results if r["success"])
            failed    = len(results) - succeeded
            print()
            print(bold(f"Processed {len(results)} line(s): "
                       f"{green(str(succeeded) + ' decoded')}, "
                       f"{(red(str(failed) + ' failed')) if failed else '0 failed'}"))
    except FileNotFoundError as exc:
        print(red(str(exc)))
        return 1
    return 0


def cmd_brute(args: argparse.Namespace) -> int:
    """Handle the `brute` sub-command — try all decoders."""
    data = args.input
    print(bold(f"Brute-force decode: trying all encodings on input"))
    print(f"  Input: {data}")
    print()

    results = try_all_decoders(data)
    shown = 0
    for enc, result, success in results:
        if not success:
            if args.show_failures:
                print(f"  {red('✗')} {enc:<12} {red(result)}")
            continue
        print(f"  {green('✓')} {cyan(enc):<22} {result}")
        shown += 1

    if shown == 0:
        print(yellow("  No decoder produced a successful result."))

    # Special case: Caesar brute-force
    if args.caesar:
        print()
        print(bold("Caesar brute-force (shifts 1–25):"))
        for shift, decoded in decode_caesar_all(data):
            print(f"  shift {shift:>2}: {decoded}")

    return 0


def _encode_data(data: str, encoding: str) -> tuple:
    """
    Encode a plaintext string using the specified encoding format.

    Args:
        data:     Plain text string to encode.
        encoding: Target encoding name (case-insensitive).

    Returns:
        Tuple of (encoded_string, success).
    """
    import base64
    from urllib.parse import quote
    import html

    enc = encoding.lower().strip()

    try:
        if enc in ("base64", "b64"):
            result = base64.b64encode(data.encode("utf-8")).decode("ascii")
            return result, True

        elif enc in ("base32", "b32"):
            result = base64.b32encode(data.encode("utf-8")).decode("ascii")
            return result, True

        elif enc in ("hex",):
            result = data.encode("utf-8").hex()
            return result, True

        elif enc in ("binary", "bin"):
            bits = "".join(format(byte, "08b") for byte in data.encode("utf-8"))
            # Group into 8-bit chunks separated by spaces for readability
            result = " ".join(bits[i:i+8] for i in range(0, len(bits), 8))
            return result, True

        elif enc in ("url",):
            result = quote(data, safe="")
            return result, True

        elif enc in ("html",):
            result = html.escape(data)
            return result, True

        elif enc in ("rot13",):
            table = str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            )
            return data.translate(table), True

        elif enc in ("morse",):
            CHAR_TO_MORSE = {
                "A": ".-",   "B": "-...", "C": "-.-.", "D": "-..",
                "E": ".",    "F": "..-.", "G": "--.",  "H": "....",
                "I": "..",   "J": ".---", "K": "-.-",  "L": ".-..",
                "M": "--",   "N": "-.",   "O": "---",  "P": ".--.",
                "Q": "--.-", "R": ".-.",  "S": "...",  "T": "-",
                "U": "..-",  "V": "...-", "W": ".--",  "X": "-..-",
                "Y": "-.--", "Z": "--..",
                "0": "-----", "1": ".----", "2": "..---", "3": "...--",
                "4": "....-", "5": ".....", "6": "-....", "7": "--...",
                "8": "---..", "9": "----.",
            }
            words = data.upper().split()
            encoded_words = []
            for word in words:
                chars = []
                for ch in word:
                    if ch in CHAR_TO_MORSE:
                        chars.append(CHAR_TO_MORSE[ch])
                    else:
                        return f"Cannot encode character '{ch}' to Morse", False
                encoded_words.append(" ".join(chars))
            return " / ".join(encoded_words), True

        else:
            return f"Encoding not supported: {encoding}. Supported: base64, base32, hex, binary, url, html, rot13, morse", False

    except Exception as exc:
        return f"Encode error: {exc}", False


def cmd_encode(args) -> int:
    """
    Handle the `encode` sub-command.

    Encodes a plaintext string into the specified format and prints the result.
    """
    data = args.input
    encoding = args.encoding

    result, success = _encode_data(data, encoding)

    if success:
        print(bold(f"Encoded [{cyan(encoding)}]:"))
        print(green(result))
        if args.json:
            import json
            payload = {"input": data, "encoding": encoding, "result": result, "success": True}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(red(f"Encode failed: {result}"))
        return 1

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Handle the `stats` sub-command."""
    try:
        stats = file_stats(args.file)
    except FileNotFoundError as exc:
        print(red(str(exc)))
        return 1

    print(bold(f"File statistics: {args.file}"))
    print(f"  Total lines:   {stats['total_lines']}")
    print(f"  Decoded lines: {green(str(stats['decoded_lines']))}")
    print(f"  Failed lines:  {red(str(stats['failed_lines']))}")
    print()
    if stats["encoding_counts"]:
        print(bold("Encoding breakdown:"))
        for enc, count in stats["encoding_counts"].items():
            print(f"  {cyan(enc):<14} {count}")
    else:
        print(yellow("No encodings detected in file."))

    return 0


# ---------------------------------------------------------------------------
# Interactive shell
# ---------------------------------------------------------------------------

SHELL_BANNER = r"""
  ___       _        ____      _                 _____ _            __
 / _ \ _   | |_ ___ / ___|   _| |__   ___ _ __  / ____| |__   ___ / _|
/ /_\ | | | | __/ _ \ |  | | | | '_ \ / _ | '__|| |    | '_ \ / _ | |_
/ ___ | |_| | || (_) | |__| |_| | |_) |  __| |   | |____| | | |  __|  _|
/_/   \_\__,_|\__\___/\____\__, |_.__/ \___|_|    \_____|_| |_|\___|_|
                            |___/
"""

SHELL_HELP = """
Available commands:
  decode  <string>              Auto-detect and decode a string
  decode  <string> -e <enc>     Decode with a specific encoding
  detect  <string>              Show possible encodings
  detect  <string> -c           Show confidence scores
  auto    <string>              Multi-layer auto decode
  brute   <string>              Try all decoders
  history                       Show command history
  clear                         Clear the screen
  help                          Show this help message
  exit / quit / Ctrl+C          Exit the shell

Supported encodings:  base64  base32  hex  binary  url  rot13  morse  html  caesar

Examples:
  decode SGVsbG8=
  decode 48656c6c6f -e hex
  auto U0dWc2JIOD0=
  detect ".... . .-.. .-.. ---"
  brute "Uryyb Jbeyq"
"""

# Map shell command names to the internal encoding identifier
_ENC_ALIASES = {
    "base64": "base64", "b64": "base64",
    "base32": "base32", "b32": "base32",
    "hex":    "hex",
    "bin":    "binary", "binary": "binary",
    "url":    "url",
    "rot13":  "rot13",  "rot":    "rot13",
    "morse":  "morse",
    "html":   "html",
    "caesar": "caesar",
}


def _shell_parse(line: str):
    """
    Parse a raw shell input line into (command, positional_args, flags).

    Supports a minimal flag syntax:
        -e <encoding>   Force a specific encoding for decode
        -c              Show confidence scores for detect

    Args:
        line: Raw user input string.

    Returns:
        Tuple of (command_str, list_of_positional_args, dict_of_flags).
        Returns (None, [], {}) for empty input.
    """
    import shlex
    try:
        tokens = shlex.split(line.strip())
    except ValueError:
        # Unmatched quotes — treat the whole line literally
        tokens = line.strip().split()

    if not tokens:
        return None, [], {}

    command = tokens[0].lower()
    positional = []
    flags = {}
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-e", "--encoding") and i + 1 < len(tokens):
            flags["encoding"] = tokens[i + 1].lower()
            i += 2
        elif tok in ("-c", "--confidence"):
            flags["confidence"] = True
            i += 1
        elif tok in ("--show-failures", "--failures"):
            flags["show_failures"] = True
            i += 1
        elif tok in ("-v", "--verbose"):
            flags["verbose"] = True
            i += 1
        elif tok in ("-n", "--max-layers") and i + 1 < len(tokens):
            try:
                flags["max_layers"] = int(tokens[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            positional.append(tok)
            i += 1

    return command, positional, flags


def _shell_decode(data: str, flags: dict) -> None:
    """Execute a decode command inside the shell."""
    enc_raw = flags.get("encoding")
    if enc_raw:
        enc = _ENC_ALIASES.get(enc_raw, enc_raw)
        result, success = decode_by_name(enc, data)
        if success:
            print(f"  {bold('Encoding:')} {cyan(enc)}")
            print(f"  {bold('Result:  ')} {green(result)}")
        else:
            print(red(f"  Decode failed: {result}"))
    else:
        from autochef.detector import detect_encoding
        encodings = detect_encoding(data)
        if not encodings:
            print(yellow("  No recognizable encoding detected."))
            return
        chosen = encodings[0]
        result, success = decode_by_name(chosen, data)
        if success:
            print(f"  {bold('Detected:')} {cyan(chosen)}")
            print(f"  {bold('Result:  ')} {green(result)}")
        else:
            print(red(f"  Detected {chosen} but decode failed: {result}"))


def _shell_detect(data: str, flags: dict) -> None:
    """Execute a detect command inside the shell."""
    if flags.get("confidence"):
        from autochef.detector import get_encoding_confidence
        scores = get_encoding_confidence(data)
        if not scores:
            print(yellow("  No encodings detected."))
            return
        print(f"  {bold('Confidence scores:')}")
        for enc, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            bar = '█' * int(score * 20) + '░' * (20 - int(score * 20))
            print(f"    {cyan(enc):<14} {bar} {score * 100:.1f}%")
    else:
        from autochef.detector import detect_encoding
        encodings = detect_encoding(data)
        if not encodings:
            print(yellow("  No encodings detected."))
            return
        print(f"  {bold('Possible encodings:')}")
        for enc in encodings:
            print(f"    - {cyan(enc)}")


def _shell_auto(data: str, flags: dict) -> None:
    """Execute an auto command inside the shell."""
    verbose = flags.get("verbose", False)
    max_layers = flags.get("max_layers", 10)
    steps, final = auto_decode(data, max_layers=max_layers, verbose=verbose)
    if not steps:
        print(yellow("  No encodings detected — input may already be plaintext."))
        print(f"  {data}")
        return
    print(f"  {bold(str(len(steps)) + ' layer(s) found:')}")
    for i, (encoding, before, after) in enumerate(steps, start=1):
        trunc = after if len(after) <= 60 else after[:57] + "..."
        print(f"    Layer {i}: [{cyan(encoding)}]  →  {trunc}")
    print(f"  {bold('Final:')} {green(final)}")


def _shell_brute(data: str, flags: dict) -> None:
    """Execute a brute command inside the shell."""
    results = try_all_decoders(data)
    shown = 0
    for enc, result, success in results:
        if not success:
            if flags.get("show_failures"):
                print(f"    {red('✗')} {enc:<12} {red(result)}")
            continue
        print(f"    {green('✓')} {cyan(enc):<18} {result}")
        shown += 1
    if shown == 0:
        print(yellow("  No decoder produced a successful result."))

def _shell_encode(data: str, flags: dict) -> None:
    """Execute an encode command inside the shell."""
    enc = flags.get("encoding")
    if not enc:
        print(yellow("  Usage: encode <string> -e <encoding>"))
        print(yellow("  Supported: base64, base32, hex, binary, url, html, rot13, morse"))
        return
    result, success = _encode_data(data, enc)
    if success:
        print(f"  {bold('Encoding:')} {cyan(enc)}")
        print(f"  {bold('Result:  ')} {green(result)}")
    else:
        print(red(f"  {result}"))


def cmd_shell(args: argparse.Namespace) -> int:
    """
    Launch the AutoCyberChef interactive shell.

    Provides a REPL (Read-Eval-Print Loop) where the user can run decode,
    detect, auto, and brute commands without restarting the program.  Command
    history is maintained for the session (↑/↓ navigation where supported).

    Args:
        args: Parsed argparse namespace (unused; kept for handler signature).

    Returns:
        Exit code (always 0 unless a fatal error occurs).
    """
    # Enable readline history if available (Unix/macOS)
    try:
        import readline
        readline.parse_and_bind("tab: complete")
        _history: list = []
    except ImportError:
        readline = None
        _history: list = []

    print(cyan(SHELL_BANNER.strip()))
    print(bold("  AutoCyberChef Interactive Shell") + "  (type 'help' for commands, 'exit' to quit)\n")

    session_history: list = []  # Track commands for the `history` built-in

    while True:
        try:
            raw = input(bold(cyan("autochef")) + bold(" > ")).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{yellow('Goodbye!')}")
            break

        if not raw:
            continue

        session_history.append(raw)
        command, positional, flags = _shell_parse(raw)

        # ---- built-ins ----
        if command in ("exit", "quit", "q"):
            print(yellow("Goodbye!"))
            break

        if command == "help":
            print(SHELL_HELP)
            continue

        if command == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue

        if command == "history":
            if not session_history:
                print(yellow("  No history yet."))
            else:
                for i, entry in enumerate(session_history[:-1], start=1):  # exclude 'history' itself
                    print(f"  {i:>3}  {entry}")
            continue

        # ---- decode / detect / auto / brute ----
        if command not in ("decode", "detect", "auto", "brute", "encode"):
            print(red(f"  Unknown command: '{command}'  —  type 'help' for available commands."))
            continue

        if not positional:
            print(yellow(f"  Usage: {command} <string>  (wrap strings with spaces in quotes)"))
            continue

        # Re-join positional tokens in case the user didn't quote their input
        data = " ".join(positional)

        print()
        try:
            if command == "decode":
                _shell_decode(data, flags)
            elif command == "detect":
                _shell_detect(data, flags)
            elif command == "auto":
                _shell_auto(data, flags)
            elif command == "brute":
                _shell_brute(data, flags)
            elif command == "encode":
                _shell_encode(data, flags)
        except Exception as exc:
            print(red(f"  Error: {exc}"))
            if os.environ.get("AUTOCHEF_DEBUG"):
                import traceback
                traceback.print_exc()
        print()

    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="autochef",
        description=(
            "AutoCyberChef — automatic encoding detection and decoding.\n"
            "A lightweight CLI tool for CTF, security analysis, and data processing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py shell                    # interactive mode\n"
            "  python main.py decode SGVsbG8=\n"
            "  python main.py detect 48656c6c6f\n"
            "  python main.py auto U0dWc2JIOD0=\n"
            "  python main.py decode-file encoded.txt\n"
            "  python main.py brute SGVsbG8= --caesar\n"
        ),
    )
    parser.add_argument("--version", action="version", version="AutoCyberChef 1.0.0")

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ---- detect ----
    p_detect = sub.add_parser("detect", help="Detect possible encodings in a string")
    p_detect.add_argument("input", help="String to analyse")
    p_detect.add_argument("-c", "--confidence", action="store_true",
                          help="Show confidence scores for each detected encoding")

    # ---- decode ----
    p_decode = sub.add_parser("decode", help="Decode a string (auto-detect or specify encoding)")
    p_decode.add_argument("input", help="Encoded string to decode")
    p_decode.add_argument("-e", "--encoding",
                          help="Force a specific encoding (base64, hex, binary, url, rot13, morse, caesar, html, base32)")
    p_decode.add_argument("--json", action="store_true", help="Output result as JSON")

    # ---- auto ----
    p_auto = sub.add_parser("auto", help="Auto decode nested/multi-layer encodings")
    p_auto.add_argument("input", help="Multiply-encoded string to decode")
    p_auto.add_argument("-n", "--max-layers", type=int, default=10, metavar="N",
                        help="Maximum decode layers (default: 10)")
    p_auto.add_argument("-v", "--verbose", action="store_true",
                        help="Print step-by-step pipeline progress")
    p_auto.add_argument("--json", action="store_true", help="Output result as JSON")

    # ---- decode-file ----
    p_file = sub.add_parser("decode-file", help="Batch decode every line of a file")
    p_file.add_argument("file", help="Path to the input file")
    p_file.add_argument("-o", "--output", metavar="FILE",
                        help="Write decoded output to FILE instead of stdout")
    p_file.add_argument("-e", "--encoding",
                        help="Force a specific encoding for all lines")
    p_file.add_argument("-l", "--layers", action="store_true",
                        help="Show multi-layer decode info for each line")
    p_file.add_argument("--blob", action="store_true",
                        help="Treat entire file as one string instead of line-by-line")
    p_file.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    # ---- brute ----
    p_brute = sub.add_parser("brute", help="Try all decoders and show every output")
    p_brute.add_argument("input", help="String to brute-force decode")
    p_brute.add_argument("--show-failures", action="store_true",
                         help="Also show failed decode attempts")
    p_brute.add_argument("--caesar", action="store_true",
                         help="Also show all 25 Caesar cipher shifts")

    # ---- encode ----
    p_encode = sub.add_parser("encode", help="Encode a plaintext string into a target format")
    p_encode.add_argument("input", help="Plain text string to encode")
    p_encode.add_argument(
        "-e", "--encoding", required=True,
        help="Target encoding: base64, base32, hex, binary, url, html, rot13, morse"
    )
    p_encode.add_argument("--json", action="store_true", help="Output result as JSON")
    
    # ---- stats ----
    p_stats = sub.add_parser("stats", help="Show encoding statistics for a file")
    p_stats.add_argument("file", help="Path to the input file")

    # ---- shell ----
    sub.add_parser(
        "shell",
        help="Launch the interactive shell (REPL)",
        description=(
            "Start an interactive AutoCyberChef session.\n"
            "Supports: decode, detect, auto, brute, history, clear, help, exit.\n"
            "Use ↑/↓ arrow keys to navigate command history (Unix/macOS)."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Parse arguments and dispatch to the appropriate command handler."""
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "detect":      cmd_detect,
        "decode":      cmd_decode,
        "auto":        cmd_auto,
        "decode-file": cmd_decode_file,
        "brute":       cmd_brute,
        "stats":       cmd_stats,
        "shell":       cmd_shell,
        "encode":      cmd_encode,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as exc:
        print(red(f"Unexpected error: {exc}"))
        if os.environ.get("AUTOCHEF_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
