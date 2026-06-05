"""Add /frontend/js/config.js script tag before api.js in all HTML pages."""
import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG_TAG = '<script src="/frontend/js/config.js"></script>'
API_TAG    = '<script src="/frontend/js/api.js"></script>'

pages = list(pathlib.Path("frontend/pages").glob("*.html"))
pages.append(pathlib.Path("frontend/index.html"))
pages = [p for p in pages if p.name != "login.html"]  # already done

for p in pages:
    text = p.read_text(encoding="utf-8")
    if CONFIG_TAG in text:
        print(f"  ALREADY  {p.name}")
        continue
    if API_TAG in text:
        text = text.replace(API_TAG, CONFIG_TAG + "\n  " + API_TAG)
        p.write_text(text, encoding="utf-8")
        print(f"  FIXED    {p.name}")
    else:
        print(f"  SKIP     {p.name} (no api.js tag found)")
