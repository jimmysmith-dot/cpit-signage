# CPIT Signage Development Guide

## Working Directory

```text
/opt/cpit-signage
```

## Git Workflow

Start from `main`:

```bash
git switch main
git status
```

Create a feature branch:

```bash
git switch -c feature/example-feature
```

After implementation and testing:

```bash
git add <intended-files>
git commit -m "Add example feature"
```

Merge:

```bash
git switch main
git merge --no-ff feature/example-feature
```

Tag a completed release:

```bash
git tag -a v0.5.1 -m "CPIT Signage v0.5.1 - Create Sign designer"
```

## Versioning

Use semantic-style versions:

- Minor release: new customer-facing feature
- Patch release: bug fix or small improvement
- Major release: production milestone or breaking change

Examples:

- `v0.5.1` — Create Sign designer
- `v0.5.2` — designer refinements
- `v0.6.0` — video support
- `v1.0.0` — supported production release

## Backup Files

Do not store active backup files inside `app/templates`, `app/static`, or `app/routes`.

Recommended:

```text
/opt/cpit-signage/backups/
```

Ensure `.gitignore` contains:

```gitignore
backups/
*.old
*.bak
*.1
```

Avoid filenames such as:

```text
admin.js.1
admin.html1
app/templates/admin.js
```

inside the active repository structure.

## Runtime Data

Recommended `.gitignore` entries:

```gitignore
venv/
__pycache__/
*.py[cod]
logs/
cache/
config/*.db
media/*
!media/.gitkeep
backups/
```

## Python Syntax Checks

```bash
cd /opt/cpit-signage

./venv/bin/python -m py_compile \
    app/app.py \
    app/__init__.py \
    app/routes/admin.py \
    app/routes/api.py \
    app/routes/player.py \
    app/services/database.py \
    app/services/slide_generator.py
```

No output means compilation succeeded.

## JavaScript Checks

At minimum, serve and inspect the active file:

```bash
curl -s http://127.0.0.1:5000/static/js/admin.js \
    | head
```

Search for expected functions:

```bash
grep -n "createSign" app/static/js/admin.js
grep -n "deleteMedia" app/static/js/admin.js
grep -n "saveRowOrder" app/static/js/admin.js
```

Use browser developer tools to check for console errors.

## Manual Regression Test

After any administration-interface change, verify:

- Admin page loads.
- Create Sign preview updates.
- Create Sign generates a PNG.
- Image upload works by click.
- Image upload works by drag and drop.
- Playlist reordering works using the handle.
- Duration edits save.
- Enabled changes save.
- Delete confirmation appears.
- Delete removes the row and file.
- Player polling detects all changes.
- Chromium remains in kiosk mode.

## Service Restart

```bash
sudo systemctl restart cpit-player
sudo systemctl status cpit-player --no-pager -l
```

Static JavaScript and HTML may still be cached by the browser. Use:

```text
Ctrl+Shift+R
```

## Direct API Testing

Create sign:

```bash
curl -s \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Test",
      "body": "Development validation",
      "footer": "",
      "background_color": "#153A5B",
      "text_color": "#FFFFFF",
      "accent_color": "#75B9E6",
      "alignment": "center",
      "duration": 5
    }' \
    http://127.0.0.1:5000/api/slides/create \
    | python3 -m json.tool
```

## Suggested Test Strategy

Near-term:

- Python unit tests for database functions
- API tests using Flask's test client
- File-generation test for Pillow output
- JavaScript linting
- HTML validation
- A smoke-test script that checks all key endpoints

Long-term:

- Integration test on a clean Debian VM
- Release installation test
- Player watchdog test
- Upgrade and rollback test
