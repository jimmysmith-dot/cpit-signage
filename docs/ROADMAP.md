# CPIT Signage Roadmap

This roadmap separates immediate production readiness from future product expansion.

## Current Milestone — v0.5.1

### Create Sign Designer

Status: substantially implemented, final validation pending.

- [x] Server-side 1920×1080 PNG generation
- [x] Title, body, and footer
- [x] Background, text, and accent colors
- [x] Alignment selection
- [x] Duration selection
- [x] Live browser preview
- [x] Generated sign added to SQLite
- [x] Generated sign added to player playlist
- [x] Redesigned administration interface
- [ ] Complete regression test
- [ ] Commit final UI files
- [ ] Merge feature branch
- [ ] Tag `v0.5.1`

## Production-Readiness Follow-Up

Recommended before broader deployment:

- [ ] Admin authentication
- [ ] CSRF protection
- [ ] Backup and restore procedure tested
- [ ] Application version shown from a single source
- [ ] Requirements file committed
- [ ] Installer or provisioning script
- [ ] Clean deployment test on a second device
- [ ] Documented customer handoff procedure
- [ ] Remote access ownership and recovery plan
- [ ] Disable unnecessary desktop services
- [ ] Add log rotation

## v0.5.2 — Designer Refinements

- [ ] Starter templates
- [ ] Background-image support
- [ ] Adjustable dark overlay
- [ ] Logo upload and positioning
- [ ] QR-code generation
- [ ] Better preview matching
- [ ] Save and reuse property branding
- [ ] Edit existing generated signs

## v0.6.0 — Video Support

- [ ] MP4 support
- [ ] WebM support
- [ ] Video-duration handling
- [ ] Play-to-completion behavior
- [ ] Upload validation
- [ ] Video thumbnails
- [ ] Hardware playback testing on DX-3000

## v0.7.0 — Scheduling

- [ ] Start and end dates
- [ ] Start and end times
- [ ] Day-of-week scheduling
- [ ] Recurring schedules
- [ ] Priority and override content
- [ ] Automatic expiration
- [ ] Time-zone configuration

## v0.8.0 — Security and Users

- [ ] Administrator login
- [ ] Password hashing
- [ ] Session security
- [ ] User roles
- [ ] Audit log
- [ ] HTTPS behind a reverse proxy
- [ ] Recovery account process

## v0.9.0 — Player Management

- [ ] Player identity
- [ ] Player health reporting
- [ ] Last-seen time
- [ ] Disk and memory status
- [ ] Remote screenshot
- [ ] Remote restart
- [ ] Remote software update
- [ ] Multiple screens per property

## v1.0.0 — Supported Production Release

- [ ] Installer or image
- [ ] Upgrade path
- [ ] Rollback path
- [ ] Complete documentation
- [ ] Backup and recovery
- [ ] Security review
- [ ] Hardware compatibility list
- [ ] Customer deployment checklist
- [ ] Support and maintenance policy
- [ ] Licensing decision
