"""
Add Firebase CDN script tags + firebase.js to all authenticated pages.
These are needed so Auth.logout() can call FirebaseAuth.signOutUser().
Skips login.html (already done) and pages that already have the tags.
"""
import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIREBASE_APP  = '<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>'
FIREBASE_AUTH = '<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"></script>'
FIREBASE_JS   = '<script src="/frontend/js/firebase.js"></script>'
CONFIG_TAG    = '<script src="/frontend/js/config.js"></script>'
API_TAG       = '<script src="/frontend/js/api.js"></script>'

pages = list(pathlib.Path("frontend/pages").glob("*.html"))
pages.append(pathlib.Path("frontend/index.html"))
pages = [p for p in pages if p.name != "login.html"]

for p in pages:
    text = p.read_text(encoding="utf-8")
    changed = False

    # Insert Firebase CDN tags before config.js if not already present
    if FIREBASE_APP not in text and CONFIG_TAG in text:
        cdn_block = FIREBASE_APP + "\n  " + FIREBASE_AUTH + "\n  "
        text = text.replace(CONFIG_TAG, cdn_block + CONFIG_TAG)
        changed = True

    # Insert firebase.js after config.js and before api.js if not already present
    if FIREBASE_JS not in text and CONFIG_TAG in text and API_TAG in text:
        text = text.replace(
            CONFIG_TAG + "\n  " + API_TAG,
            CONFIG_TAG + "\n  " + FIREBASE_JS + "\n  " + API_TAG,
        )
        changed = True

    if changed:
        p.write_text(text, encoding="utf-8")
        print(f"  FIXED  {p.name}")
    else:
        print(f"  OK     {p.name}")

print("Done.")
