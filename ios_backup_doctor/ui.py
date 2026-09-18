"""Terminal output helpers. No dependencies, degrades to plain text when piped."""
from __future__ import annotations

import os
import shutil
import sys

_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def bold(t: str) -> str:   return _c("1", t)
def dim(t: str) -> str:    return _c("2", t)
def red(t: str) -> str:    return _c("31", t)
def green(t: str) -> str:  return _c("32", t)
def yellow(t: str) -> str: return _c("33", t)
def blue(t: str) -> str:   return _c("34", t)


OK, WARN, BAD, INFO = "✓", "!", "✗", "·"


def width() -> int:
    return min(shutil.get_terminal_size((80, 24)).columns, 78)


def rule(char: str = "─") -> None:
    print(dim(char * width()))


def heading(text: str) -> None:
    print()
    print(bold(text))
    rule()


def item(symbol: str, label: str, value: str = "", note: str = "") -> None:
    colour = {OK: green, WARN: yellow, BAD: red}.get(symbol, dim)
    line = f"  {colour(symbol)} {label}"
    if value:
        pad = max(1, 34 - len(label))
        line += " " * pad + bold(value)
    if note:
        line += dim(f"   {note}")
    print(line)


def verdict(symbol: str, title: str, body: str = "") -> None:
    colour = {OK: green, WARN: yellow, BAD: red}.get(symbol, blue)
    print()
    print(colour(bold(f"  {symbol}  {title}")))
    if body:
        print()
        for line in body.strip().splitlines():
            print(f"     {line}")
    print()


def step(text: str) -> None:
    print(dim(f"  … {text}"), flush=True)


def human_bytes(n: int) -> str:
    if n >= 2**30:
        return f"{n / 2**30:.2f} GB"
    if n >= 2**20:
        return f"{n / 2**20:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n} B"
