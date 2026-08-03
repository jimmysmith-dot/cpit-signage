# CPIT Signage Architecture

## Design Goals

CPIT Signage is designed around the following priorities:

- Low deployment cost
- Local and remote administration
- Offline playback
- Simple player behavior
- Minimal dependencies
- Recoverability after power loss
- Easy support through SSH and Tailscale
- Future compatibility with centralized fleet management

## High-Level Components

### 1. Chromium Player

Chromium displays a local webpage from:

```text
http://127.0.0.1:5000/
```

Its responsibilities are intentionally limited:

- Request the active playlist
- Display image content
- Transition between slides
- Poll for playlist changes
- Continue looping

The player does not directly manage the database or contact a cloud service.

### 2. Flask Application

Flask provides:

- Player page
- Administration page
- REST API
- Media-file serving
- Sign-generation requests

The application currently listens on localhost. Remote browser access is provided through an SSH tunnel or Tailscale-supported workflow.

### 3. JavaScript Player Engine

The player JavaScript:

- Loads `/api/slides`
- Creates a signature of the playlist
- Polls approximately every 15 seconds
- Detects content, order, duration, or enable-state changes
- Applies playlist changes without restarting Chromium
- Uses fade transitions
- Maintains the current slide where possible

### 4. Administration Interface

The administration interface provides:

- Upload controls
- Playlist table
- Drag-and-drop reordering
- Duration editing
- Enable and disable controls
- Delete controls
- Create Sign designer
- Live sign preview
- Media count and basic status display

### 5. SQLite Database

Database location:

```text
/opt/cpit-signage/config/signage.db
```

Current media records include:

- ID
- Filename
- Media type
- Duration
- Sort order
- Enabled state
- Created timestamp

SQLite was selected because it:

- Requires no separate database service
- Is well suited for a single-player appliance
- Is easy to back up
- Supports future migration to a larger server database

### 6. Media Directory

Media location:

```text
/opt/cpit-signage/media
```

The directory stores:

- Uploaded JPG images
- Uploaded PNG images
- Uploaded GIF images
- Uploaded WebP images
- Server-generated PNG signs

The media directory is runtime data and should normally be excluded from Git.

### 7. Sign Generator

The sign generator uses Pillow to render:

- 1920×1080 PNG output
- Title
- Body text
- Footer
- Background color
- Text color
- Accent color
- Left, center, or right alignment
- Automatic text wrapping
- Available system fonts

The generated sign is inserted into the normal media table. The player sees it only as another image. This keeps the playback architecture simple.

## Request Flows

### Image Upload

```text
Browser
  -> POST /api/media
  -> validate extension and image contents
  -> save unique filename
  -> insert SQLite media record
  -> return JSON
  -> admin page reloads
  -> player detects change during polling
```

### Create Sign

```text
Browser
  -> POST /api/slides/create
  -> validate text, colors, alignment, and duration
  -> Pillow generates PNG
  -> save PNG in media directory
  -> insert SQLite media record
  -> return JSON
  -> admin page reloads
  -> player detects change during polling
```

### Reorder

```text
Browser drag operation
  -> PUT /api/media/reorder
  -> validate complete unique ID list
  -> update SQLite sort_order values
  -> player detects changed playlist signature
```

### Delete

```text
Browser
  -> DELETE /api/media/{id}
  -> delete SQLite record
  -> delete media file
  -> renumber remaining playlist
  -> player detects changed playlist
```

## Reliability Model

The player and content are local. If Internet access is lost:

- Chromium continues displaying locally stored content.
- SQLite remains available.
- The local admin page remains available on the appliance.
- Remote management is unavailable until connectivity returns.

## Security Boundary

The Flask application currently binds to localhost. This limits direct network exposure.

Preferred remote methods:

- SSH tunnel
- Tailscale
- Future authenticated reverse proxy

Do not directly expose the Flask development server to the public Internet.

## Future Architecture

A future central management service could add:

```text
CPIT Signage Manager
        |
        +---- Player registration
        +---- Content distribution
        +---- Scheduling
        +---- Health reporting
        +---- Remote screenshots
        +---- Fleet updates
        |
        +---- Local players continue using local cache
```

The current player architecture can remain largely unchanged. A future sync service can update the same local SQLite database and media directory.
