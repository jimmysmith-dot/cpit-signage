# Changelog

All notable changes to CPIT Signage are documented here.

## [Unreleased]

### Added

- Documentation package
- Installation guide
- Architecture guide
- API reference
- Operations guide
- Development guide
- Release checklist
- Security notes

## [0.5.1] - Development

### Added

- Server-side Create Sign functionality
- `POST /api/slides/create`
- 1920×1080 PNG rendering with Pillow
- Automatic text wrapping
- Title, message, and footer support
- Configurable background, text, and accent colors
- Left, center, and right alignment
- Configurable display duration
- Live 16:9 preview
- Redesigned administration interface
- Media count and page-load status display

### Notes

- Release is not final until regression testing, merge, and tag are complete.
- Generated signs are stored as ordinary image media.

## [0.5.0]

### Added

- Complete media-management workflow
- Media deletion
- Drag-and-drop playlist ordering
- Playlist renumbering after deletion
- Browser confirmation before permanent deletion

## [0.4.3]

### Added

- Automatic player playlist polling
- Playlist-change detection
- Live duration, enable-state, order, upload, and deletion updates
- No Chromium restart required for playlist changes

## [0.4.2]

### Added

- Drag-and-drop image uploads
- Browser file picker
- Multiple-file uploads
- `POST /api/media`
- Pillow image validation
- Unique stored filenames
- Upload-size configuration

### Fixed

- Upload JavaScript waits for the DOM.
- Browser default file-drop navigation is prevented.

## [0.4.1]

### Added

- REST media-management API
- `GET /api/media`
- `GET /api/media/{id}`
- `PUT /api/media/{id}`
- `DELETE /api/media/{id}`
- JSON validation and API errors

## [0.4.0]

### Changed

- Refactored the Flask application into Blueprints.
- Separated player, API, and admin routes.
- Moved database logic into the services package.
- Updated systemd launch to Python module mode.

## [0.3.1]

### Added

- Local administration interface
- Media thumbnails
- Duration editing
- Manual order editing
- Enable and disable controls
- Playlist-save confirmation

## [0.3.0]

### Added

- SQLite media database
- Automatic existing-media import
- Database-backed playlist API

## [0.2.0]

### Added

- JavaScript slideshow engine
- Smooth fade transitions
- Automatic looping
- `/api/slides`
- Local media serving

## [0.1.0]

### Added

- Debian 13 appliance foundation
- Networking
- SSH
- XFCE
- Chromium kiosk mode
- Automatic startup
- Flask systemd service
- Git repository
