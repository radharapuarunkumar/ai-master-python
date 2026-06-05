import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 1. config.js key lines
cfg = pathlib.Path("frontend/js/config.js").read_text(encoding="utf-8")
print("=== config.js key lines ===")
for line in cfg.splitlines():
    stripped = line.strip()
    if any(k in stripped for k in ["GOOGLE_CLIENT_ID", "API_BASE", "REDIRECT", "GOOGLE_REDIRECT"]):
        print(" ", stripped)

# 2. Script load order in each page
print("\n=== Script load order per page ===")
for p in sorted(pathlib.Path("frontend").rglob("*.html")):
    text = p.read_text(encoding="utf-8")
    tags = [l.strip() for l in text.splitlines() if "<script src=" in l]
    names = []
    for t in tags:
        try:
            names.append(t.split("/")[-1].split('"')[0])
        except Exception:
            pass
    print(f"  {p.name:<22} {' -> '.join(names)}")

# 3. login.html emoji spot-check
print("\n=== login.html emoji lines ===")
login_text = pathlib.Path("frontend/pages/login.html").read_text(encoding="utf-8")
count = 0
for line in login_text.splitlines():
    stripped = line.strip()
    if any(ord(c) > 0x1F00 for c in stripped) and stripped:
        print(" ", stripped[:90])
        count += 1
        if count >= 8:
            break
