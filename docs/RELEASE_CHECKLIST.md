# CPIT Signage Release Checklist

Use this checklist before every tag.

## 1. Source Control

- [ ] Correct feature branch is active.
- [ ] `git status` contains only intended changes.
- [ ] No temporary files are present.
- [ ] Runtime media is not staged.
- [ ] SQLite database is not staged.
- [ ] Backups are not staged.

Commands:

```bash
git branch --show-current
git status
```

## 2. Python Validation

```bash
./venv/bin/python -m py_compile \
    app/app.py \
    app/__init__.py \
    app/routes/admin.py \
    app/routes/api.py \
    app/routes/player.py \
    app/services/database.py \
    app/services/slide_generator.py
```

- [ ] No Python compile errors.

## 3. Service Validation

```bash
sudo systemctl restart cpit-player
sudo systemctl status cpit-player --no-pager -l
```

- [ ] Service is active.
- [ ] No restart loop.
- [ ] No critical journal errors.

## 4. API Smoke Test

```bash
curl -I http://127.0.0.1:5000/
curl -s http://127.0.0.1:5000/api/slides \
    | python3 -m json.tool
curl -s http://127.0.0.1:5000/api/media \
    | python3 -m json.tool
```

- [ ] Player page returns successfully.
- [ ] Slides API returns valid JSON.
- [ ] Media API returns valid JSON.

## 5. Administration Regression Test

- [ ] Admin page loads through SSH tunnel.
- [ ] Create Sign preview responds to text.
- [ ] Color controls update preview.
- [ ] Alignment updates preview.
- [ ] Create Sign generates valid PNG.
- [ ] Created sign appears in playlist.
- [ ] Upload by click works.
- [ ] Upload by drag and drop works.
- [ ] Reorder handle works.
- [ ] Duration saves.
- [ ] Enabled checkbox saves.
- [ ] Delete confirmation appears.
- [ ] Delete removes file and database record.
- [ ] Media count remains accurate.

## 6. Player Regression Test

- [ ] Player continues looping.
- [ ] Fade transition works.
- [ ] Uploaded content appears.
- [ ] Created sign appears.
- [ ] Reordered content changes order.
- [ ] Disabled content disappears.
- [ ] Deleted content disappears.
- [ ] All changes appear within polling interval.

## 7. Restart and Recovery

- [ ] Reboot appliance.
- [ ] Auto-login works.
- [ ] Flask service starts.
- [ ] Chromium kiosk starts.
- [ ] Player resumes automatically.
- [ ] Tailscale reconnects.
- [ ] SSH works.

## 8. Documentation

- [ ] README updated.
- [ ] CHANGELOG updated.
- [ ] ROADMAP updated if scope changed.
- [ ] API documentation updated.
- [ ] Version string updated.

## 9. Commit

```bash
git add <intended-files>
git commit -m "Version X.Y.Z - Release description"
```

- [ ] Commit succeeds.
- [ ] Working tree is clean.

## 10. Merge

```bash
git switch main
git merge --no-ff feature/branch-name
```

- [ ] Merge succeeds.
- [ ] Main branch passes smoke test.

## 11. Tag

```bash
git tag -a vX.Y.Z -m "CPIT Signage vX.Y.Z - Release description"
```

Verify:

```bash
git tag -n --sort=version:refname
git log --oneline --decorate -10
```

## 12. Backup

- [ ] SQLite backup created.
- [ ] Media backup created.
- [ ] Release source archived or pushed to a remote repository.
