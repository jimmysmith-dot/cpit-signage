# CPIT Signage Security Notes

## Current Security Posture

The current application is suitable for a controlled proof-of-concept environment when:

- Flask binds only to `127.0.0.1`
- Remote access occurs through SSH or Tailscale
- The Debian account uses a strong password or SSH key
- The device is not directly exposed to the public Internet

## Current Known Limitations

- No application login
- No user roles
- No CSRF protection
- No API authentication
- No HTTPS inside the local application
- Flask development server is in use
- No rate limiting
- No audit log
- Uploaded-image processing is performed in the application process
- Remote access depends on operating-system and Tailscale security

## Required Practices

### Keep Flask Local

The application should continue binding to:

```text
127.0.0.1:5000
```

Do not change it to `0.0.0.0` at customer sites without adding proper authentication, firewall restrictions, and a production web server.

### Use SSH Keys

Recommended SSH configuration after validating key access:

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
X11Forwarding no
```

Restart SSH carefully after testing:

```bash
sudo sshd -t
sudo systemctl restart ssh
```

### Protect Tailscale Access

- Use a dedicated organization or controlled tailnet.
- Remove retired players.
- Apply Tailscale ACLs when multiple customers are supported.
- Record who owns the device in Tailscale.
- Avoid sharing one unrestricted tailnet with unrelated customer systems.

### Patch the Appliance

```bash
sudo apt update
sudo apt upgrade
```

Schedule maintenance rather than allowing uncontrolled updates during display hours.

### Protect Backups

The SQLite database and media directory may contain customer content. Store backups in a controlled location.

## Recommended Before Broader Production

- Authentication for `/admin/`
- CSRF protection
- Production WSGI server
- Reverse proxy
- HTTPS
- Security headers
- Audit log
- User roles
- Upload MIME and dimension limits
- Disk quota and free-space checks
- Session timeout
- Central secrets management
- Tested account-recovery process

## Suggested Production Stack

```text
Browser
  -> Tailscale or HTTPS
  -> Nginx
  -> Gunicorn
  -> Flask
  -> SQLite
```

For a centralized multi-player service, migrate server-side data to PostgreSQL while keeping SQLite on individual players for local caching.
