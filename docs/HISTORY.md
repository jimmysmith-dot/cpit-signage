# CPIT Signage Project History

## Overview

CPIT Signage was developed by CompuPro IT Services as a lightweight,
self-hosted digital signage appliance for hospitality and commercial
customers.

The original request came from a hotel that wanted a simple way to
display remodel renderings on a lobby television. Rather than relying
on cloud subscriptions or third-party signage platforms, the goal was
to build a reliable appliance that could be remotely managed while
continuing to operate without Internet access.

---

# Design Philosophy

Several principles guided the project from the beginning.

- Keep the player simple.
- Store all content locally.
- Allow remote administration.
- Require no recurring subscription.
- Support inexpensive hardware.
- Recover automatically after power loss.
- Make future enhancements easy without redesigning the player.

---

# Development Timeline

## Phase 1

Initial proof of concept.

Features included:

- Debian installation
- Chromium kiosk mode
- Flask web server
- Automatic startup
- Local slideshow
- Image playback

---

## Phase 2

Content moved from static files into SQLite.

Benefits:

- Persistent playlist
- Sort order
- Enable/disable
- Duration control
- Foundation for future features

---

## Phase 3

Administration interface.

Added:

- Thumbnail previews
- Playlist editing
- Duration editing
- Enable/disable
- Save workflow

---

## Phase 4

REST API.

Added:

- GET media
- PUT media
- DELETE media
- Media upload
- Browser drag-and-drop
- Multiple uploads
- Automatic image validation

---

## Phase 5

Live player updates.

The player now polls the server approximately every
15 seconds and updates automatically without restarting
Chromium.

Supported updates include:

- Uploads
- Deletes
- Reordering
- Duration changes
- Enable/disable

---

## Phase 6

Create Sign Designer.

Major enhancement allowing users to create
professional-looking signage without external
design software.

Features include:

- Live preview
- 1920×1080 rendering
- Title
- Body
- Footer
- Custom colors
- Accent bar
- Alignment
- Automatic playlist integration

Generated signs are stored as ordinary image media,
allowing the player to remain completely unaware of
how the image was created.

---

# Remote Development

One significant milestone was proving that the entire
development process could occur remotely.

The proof-of-concept appliance operated behind a
Cradlepoint cellular router and was administered over
Tailscale and SSH.

This validated the intended deployment model for
customer installations.

---

# Lessons Learned

Several architectural decisions proved particularly
valuable.

SQLite simplified deployment while remaining powerful
enough for the appliance.

Separating the player from the administration interface
made future enhancements significantly easier.

Treating generated signs as ordinary media eliminated
the need for any player modifications.

Polling every fifteen seconds provided a good balance
between responsiveness and simplicity.

---

# Future Direction

Future development is expected to include:

- Templates
- Background images
- Company logos
- QR codes
- Video playback
- Scheduling
- Authentication
- Multi-player management
- Centralized administration

The long-term goal is to provide a commercial-quality
digital signage platform while maintaining the
simplicity and reliability established during the
initial development.
