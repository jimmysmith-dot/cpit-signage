# CPIT Signage REST API

Base URL:

```text
http://127.0.0.1:5000/api
```

The API is currently intended for local use by the player and administration interface. Authentication has not yet been added.

## GET `/api/slides`

Returns the enabled playlist in display order.

Example:

```bash
curl -s http://127.0.0.1:5000/api/slides \
    | python3 -m json.tool
```

Example response:

```json
[
  {
    "id": 1,
    "type": "image",
    "url": "/media/welcome.jpg",
    "duration": 10,
    "sort_order": 1
  }
]
```

## GET `/api/media`

Returns all media records, including disabled items.

```bash
curl -s http://127.0.0.1:5000/api/media \
    | python3 -m json.tool
```

## GET `/api/media/{id}`

Returns one media record.

```bash
curl -s http://127.0.0.1:5000/api/media/1 \
    | python3 -m json.tool
```

Possible status codes:

- `200 OK`
- `404 Not Found`

## POST `/api/media`

Uploads one image as multipart form data.

Supported extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.gif`
- `.webp`

Example:

```bash
curl -s \
    -X POST \
    -F "file=@example.jpg" \
    http://127.0.0.1:5000/api/media \
    | python3 -m json.tool
```

The server:

- Sanitizes the original filename
- Adds a unique suffix
- Verifies that Pillow can identify the file as an image
- Saves the file
- Creates an enabled database record
- Assigns a default duration of 10 seconds

Possible status codes:

- `201 Created`
- `400 Bad Request`
- `500 Internal Server Error`

## PUT `/api/media/{id}`

Updates duration, order, or enabled status.

Partial request example:

```bash
curl -s \
    -X PUT \
    -H "Content-Type: application/json" \
    -d '{"enabled":false}' \
    http://127.0.0.1:5000/api/media/1 \
    | python3 -m json.tool
```

Complete example:

```bash
curl -s \
    -X PUT \
    -H "Content-Type: application/json" \
    -d '{
      "duration": 15,
      "sort_order": 2,
      "enabled": true
    }' \
    http://127.0.0.1:5000/api/media/1 \
    | python3 -m json.tool
```

Validation:

- Duration: `1` through `3600`
- Sort order: zero or greater
- Enabled: JSON Boolean

## PUT `/api/media/reorder`

Updates the full playlist order.

The request must contain every current media ID exactly once.

Example:

```bash
curl -s \
    -X PUT \
    -H "Content-Type: application/json" \
    -d '{"media_ids":[2,1,3,4]}' \
    http://127.0.0.1:5000/api/media/reorder \
    | python3 -m json.tool
```

Validation:

- Non-empty array
- No `null` IDs
- No duplicate IDs
- Exact set match with current database IDs

## DELETE `/api/media/{id}`

Deletes the database record and its corresponding media file.

```bash
curl -s \
    -X DELETE \
    http://127.0.0.1:5000/api/media/1 \
    | python3 -m json.tool
```

Example response:

```json
{
  "deleted": true,
  "file_deleted": true,
  "id": 1,
  "filename": "welcome.jpg"
}
```

## POST `/api/slides/create`

Generates a 1920×1080 PNG sign and registers it as image media.

Example:

```bash
curl -s \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Lobby Remodel Update",
      "body": "Our lobby renovation begins soon.\nThank you for your patience.",
      "footer": "We appreciate you staying with us.",
      "background_color": "#153A5B",
      "text_color": "#FFFFFF",
      "accent_color": "#75B9E6",
      "alignment": "center",
      "duration": 12
    }' \
    http://127.0.0.1:5000/api/slides/create \
    | python3 -m json.tool
```

Validation:

- Title or body is required
- Title maximum: 250 characters
- Body maximum: 2,000 characters
- Footer maximum: 500 characters
- Alignment: `left`, `center`, or `right`
- Duration: `1` through `3600`

Example response:

```json
{
  "message": "Slide created successfully",
  "media": {
    "id": 12,
    "filename": "lobby-remodel-update-a1b2c3d4.png",
    "type": "image",
    "url": "/media/lobby-remodel-update-a1b2c3d4.png",
    "duration": 12,
    "sort_order": 12,
    "enabled": true,
    "created_at": "2026-08-02 18:00:00"
  }
}
```

## Media Retrieval

Media files are served outside the `/api` prefix:

```text
GET /media/{filename}
```

Example:

```text
http://127.0.0.1:5000/media/welcome.jpg
```

## Current API Limitations

- No authentication
- No CSRF protection for browser actions
- No user roles
- No audit log
- No API version prefix
- No rate limiting
- No background-job system
- No formal OpenAPI schema

These are appropriate future improvements before broad multi-user or public-network exposure.
