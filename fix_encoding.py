"""
Deep UTF-8 fix for frontend HTML files.

Problems found:
1. UTF-8 BOM (EF BB BF) at start of every HTML file — added by PowerShell Set-Content -Encoding UTF8
2. Triple/quadruple-encoded emoji — some emoji went through multiple encoding cycles
   e.g. 🗂 -> C3B0 C5B8 C2 90 C28D (still broken after first fix pass)

Strategy:
  1. Strip BOM
  2. Apply cp1252->utf-8 round-trip repair TWICE (handles double-encoded sequences)
  3. Verify no suspect cp1252 control chars remain
  4. Write back as clean UTF-8 (no BOM)
"""

import pathlib
import sys
import re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).parent / "frontend"


def fix_once(text: str) -> str:
    """One pass of cp1252-as-UTF-8 mojibake repair."""
    try:
        return text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    # Line-by-line fallback
    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        try:
            out.append(line.encode("cp1252").decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            out.append(line)
    return "".join(out)


def count_suspect(text: str) -> int:
    """Count characters that look like cp1252 printable replacements for high bytes."""
    # These Latin-extended chars (ð, Ÿ, Å, â, etc.) are suspicious when
    # they appear next to other high-code-point chars in HTML context.
    suspect = 0
    for c in text:
        if c in "ðŸÅâœ" and ord(c) < 0x400:
            suspect += 1
    return suspect


def strip_bom(text: str) -> str:
    return text.lstrip("\ufeff")


def fix_file(fpath: pathlib.Path) -> tuple[bool, str]:
    """Fix a single file. Returns (was_changed, status_message)."""
    # Read raw bytes first to detect BOM and actual encoding
    raw = fpath.read_bytes()
    has_bom = raw[:3] == b"\xef\xbb\xbf"
    if has_bom:
        raw = raw[3:]  # strip BOM bytes before decoding

    # Decode as UTF-8 (errors=replace to not crash on any remaining bad sequences)
    text = raw.decode("utf-8", errors="replace")

    # Apply fix up to 3 times (handles multiple encoding layers)
    original = text
    for _ in range(3):
        fixed = fix_once(text)
        if fixed == text:
            break
        text = fixed

    # Ensure charset meta is correct in HTML files
    if fpath.suffix == ".html":
        # Remove any existing charset meta tags (may be duplicated or wrong)
        text = re.sub(r'\s*<meta\s+charset=["\'][^"\']*["\'][^>]*>\s*', "\n  ", text, flags=re.IGNORECASE)
        # Add correct one immediately after <head>
        text = re.sub(r'(<head>)', r'\1\n  <meta charset="UTF-8">', text, count=1, flags=re.IGNORECASE)

    changed = has_bom or (text != original)
    if changed:
        fpath.write_text(text, encoding="utf-8")  # no BOM — Python's default

    suspect = count_suspect(text)
    return changed, f"{'FIXED' if changed else 'OK'} | {len([c for c in text if ord(c)>0x1F00])} emoji | {suspect} suspect chars"


def main():
    html_files = sorted(ROOT.rglob("*.html"))
    js_files   = sorted((ROOT / "js").glob("*.js"))
    css_files  = sorted((ROOT / "css").glob("*.css"))

    all_files = html_files + js_files + css_files

    print(f"Processing {len(all_files)} files...\n")

    fixed = []
    clean = []

    for fpath in all_files:
        changed, msg = fix_file(fpath)
        rel = str(fpath.relative_to(ROOT.parent))
        if changed:
            fixed.append(rel)
            print(f"  FIXED  {rel}")
            print(f"         {msg}")
        else:
            clean.append(rel)
            print(f"  OK     {rel}")
            print(f"         {msg}")

    print(f"\n{'='*60}")
    print(f"Fixed: {len(fixed)} files")
    print(f"Clean: {len(clean)} files")

    # Spot-check: print some emoji-containing lines from dashboard.html
    dash = ROOT / "pages" / "dashboard.html"
    if dash.exists():
        text = dash.read_text(encoding="utf-8")
        emoji_lines = [l.strip() for l in text.splitlines() if any(ord(c) > 0x1F00 for c in l)]
        print(f"\nSpot-check dashboard.html ({len(emoji_lines)} emoji lines):")
        for line in emoji_lines[:8]:
            print(f"  {line[:90]}")


if __name__ == "__main__":
    main()
