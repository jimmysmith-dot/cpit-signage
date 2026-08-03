# Contributing to CPIT Signage

Thank you for your interest in contributing to CPIT Signage.

This document defines the development standards, workflow, and expectations used throughout the project.

---

# Project Philosophy

CPIT Signage is designed around several core principles:

- Reliability over complexity
- Offline-first operation
- Simple deployment
- Low hardware requirements
- Clean and maintainable code
- Clear documentation
- Backward compatibility whenever practical

Every contribution should support these goals.

---

# Repository Structure

```
app/
    routes/
    services/
    static/
    templates/

config/
deployment/
docs/
media/
scripts/

README.md
LICENSE
VERSION
requirements.txt
```

New files should be placed in the appropriate directory rather than creating new top-level folders unless there is a compelling architectural reason.

---

# Branch Strategy

Development should never occur directly on the production branch.

Recommended workflow:

```
main
    │
    ├── feature/create-slide-designer
    ├── feature/video-support
    ├── feature/templates
    └── feature/player-health
```

Each feature branch should focus on one major capability.

---

# Commit Messages

Commit messages should clearly describe the completed work.

Preferred format:

```
Version 0.5.1 - Add Create Sign designer

Version 0.5.2 - Add background image support

Version 0.6.0 - Add MP4 playback
```

Avoid messages such as:

```
Fixed stuff

Changes

Update

Test
```

---

# Coding Standards

## Python

- Follow PEP 8 where practical.
- Prefer descriptive function names.
- Keep functions focused on a single responsibility.
- Validate all external input.
- Return useful error messages.
- Avoid duplicate logic.

Example:

```python
def create_media_record():
```

instead of

```python
def doStuff():
```

---

## JavaScript

- Use modern JavaScript.
- Prefer `const` and `let`.
- Avoid global variables.
- Use event delegation where appropriate.
- Keep DOM manipulation separate from API logic.

---

## HTML

- Use semantic elements.
- Maintain consistent indentation.
- Keep IDs descriptive.
- Avoid inline JavaScript.

---

## CSS

- Group related rules.
- Prefer reusable classes.
- Keep color definitions centralized.
- Avoid unnecessary specificity.

---

# Documentation

Every significant feature should update:

- README.md
- CHANGELOG.md
- ROADMAP.md (if applicable)
- API.md (if API changes)
- INSTALL.md (if deployment changes)

Code should never be significantly ahead of the documentation.

---

# Testing Requirements

Before committing:

## Python

```
python -m py_compile ...
```

No errors.

---

## Browser

Verify:

- No JavaScript console errors.
- No missing resources.
- Responsive layout remains usable.

---

## Functional

Confirm:

- Upload
- Delete
- Reorder
- Duration edits
- Enable/disable
- Polling
- Player operation
- Create Sign

---

# Pull Requests

If using GitHub in the future, pull requests should include:

- Summary
- Reason for change
- Screenshots when UI changes
- Testing performed
- Documentation updates

---

# Versioning

The project uses semantic versioning.

Examples:

```
0.5.1
```

Designer improvements.

```
0.6.0
```

Video support.

```
1.0.0
```

First supported production release.

---

# Security

Contributors should never commit:

```
venv/
config/*.db
media/*
logs/
backups/
```

Sensitive credentials must never be stored in the repository.

---

# Design Principles

When adding new features:

- Keep the player simple.
- Put complexity into the administration interface.
- Prefer generating media rather than adding player logic.
- Minimize required user interaction.
- Preserve existing customer workflows whenever possible.

---

# Documentation Before Code

Large features should begin with:

1. Design discussion
2. Architecture review
3. Development plan
4. Implementation
5. Testing
6. Documentation
7. Release

---

# Long-Term Vision

The long-term goal of CPIT Signage is to provide a professional digital signage platform for hospitality and commercial customers while maintaining the simplicity of a self-contained appliance.

Future development includes:

- Templates
- Background images
- Logos
- QR codes
- Video playback
- Scheduling
- Authentication
- Multi-player management
- Fleet administration

Every contribution should move the project toward that vision without sacrificing reliability or maintainability.

---

# Acknowledgements

CPIT Signage was developed by **CompuPro IT Services** as a practical solution for hospitality digital signage. The project has evolved through iterative development, real-world testing, and a strong emphasis on maintainable architecture.

The project philosophy has been to build software the same way it will be used in production: incrementally, with continuous testing, clear documentation, and a focus on solving real customer problems rather than adding unnecessary complexity.
