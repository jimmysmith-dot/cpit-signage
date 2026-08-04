# CPIT Signage Studio v1.0 Release Checklist

## Source and versioning

- [ ] Working tree is clean
- [ ] Feature branch has been merged into `main`
- [ ] `VERSION` contains `1.0.0`
- [ ] README reflects v1.0 capabilities
- [ ] CHANGELOG contains the v1.0 release entry
- [ ] Customer runtime data is not tracked by Git

## Static validation

- [ ] All Python files compile
- [ ] Shell scripts pass `bash -n`
- [ ] No JavaScript console errors
- [ ] No missing browser resources

## Studio functions

- [ ] Templates load and apply
- [ ] Solid-color signs publish
- [ ] Image-background signs publish
- [ ] Logos upload, select, resize, reposition, and delete
- [ ] Live preview reflects logo and background selections
- [ ] Published sign appears in the playlist
- [ ] Clear Designer works
- [ ] Success and error notifications display correctly

## Media and playlist

- [ ] Multi-image upload works
- [ ] Drag-to-reorder works
- [ ] Order persists
- [ ] Duration changes persist
- [ ] Enable/disable works
- [ ] Media deletion works
- [ ] Player polling reflects changes

## Appliance operation

- [ ] Service starts automatically
- [ ] LightDM autologin works
- [ ] Chromium launches in kiosk mode
- [ ] Address bar is not displayed
- [ ] Screen blanking is disabled
- [ ] Player recovers after application restart
- [ ] Player recovers after reboot
- [ ] Player recovers after power loss
- [ ] Offline playback works

## Installer validation on LC8810

- [ ] Start from fresh Debian 13
- [ ] Run `sudo ./install.sh`
- [ ] Installer completes without manual file edits
- [ ] Health check passes
- [ ] Reboot enters the kiosk automatically
- [ ] Administration page is reachable remotely
- [ ] Test media can be uploaded
- [ ] A branded sign can be published
- [ ] Upgrade script preserves content
- [ ] Uninstall retention option is verified

## Release

- [ ] Final regression test completed
- [ ] Commit release changes
- [ ] Create annotated `v1.0.0` tag
- [ ] Create release archive
- [ ] Store release notes and checksum
