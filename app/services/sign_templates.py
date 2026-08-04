"""Built-in sign templates for CPIT Signage Studio."""

from __future__ import annotations

from copy import deepcopy

SIGN_TEMPLATES = {
    "blank": {
        "id": "blank",
        "name": "Blank Sign",
        "description": "Start with a clean, neutral layout.",
        "title": "",
        "body": "",
        "footer": "",
        "background_color": "#153A5B",
        "text_color": "#FFFFFF",
        "accent_color": "#75B9E6",
        "alignment": "center",
        "overlay_opacity": 35,
        "duration": 10,
    },
    "remodel-update": {
        "id": "remodel-update",
        "name": "Remodel Update",
        "description": (
            "Announce renovation plans, milestones, or temporary changes."
        ),
        "title": "Lobby Remodel Update",
        "body": (
            "Our lobby renovation begins soon.\n"
            "Thank you for your patience."
        ),
        "footer": "We appreciate you staying with us.",
        "background_color": "#153A5B",
        "text_color": "#FFFFFF",
        "accent_color": "#75B9E6",
        "alignment": "center",
        "overlay_opacity": 40,
        "duration": 12,
    },
    "welcome": {
        "id": "welcome",
        "name": "Welcome",
        "description": "Create a warm guest or visitor welcome message.",
        "title": "Welcome",
        "body": "We are glad you are here.",
        "footer": "Enjoy your stay.",
        "background_color": "#1F4E5F",
        "text_color": "#FFFFFF",
        "accent_color": "#E5C07B",
        "alignment": "center",
        "overlay_opacity": 30,
        "duration": 10,
    },
    "maintenance-notice": {
        "id": "maintenance-notice",
        "name": "Maintenance Notice",
        "description": (
            "Notify guests about closures, repairs, or service interruptions."
        ),
        "title": "Maintenance Notice",
        "body": (
            "This area is temporarily unavailable while maintenance "
            "is completed."
        ),
        "footer": "We apologize for the inconvenience.",
        "background_color": "#4A3A16",
        "text_color": "#FFFFFF",
        "accent_color": "#F4C95D",
        "alignment": "center",
        "overlay_opacity": 45,
        "duration": 12,
    },
    "event": {
        "id": "event",
        "name": "Event",
        "description": "Promote an event, meeting, or scheduled activity.",
        "title": "Upcoming Event",
        "body": "Add the event name, date, time, and location here.",
        "footer": "We look forward to seeing you.",
        "background_color": "#3B2E5A",
        "text_color": "#FFFFFF",
        "accent_color": "#C7A4FF",
        "alignment": "center",
        "overlay_opacity": 35,
        "duration": 12,
    },
    "restaurant-special": {
        "id": "restaurant-special",
        "name": "Restaurant Special",
        "description": "Highlight a meal, promotion, or limited-time offer.",
        "title": "Today's Special",
        "body": "Add the featured item and price here.",
        "footer": "Available while supplies last.",
        "background_color": "#5A2E1F",
        "text_color": "#FFF8F0",
        "accent_color": "#F2B880",
        "alignment": "center",
        "overlay_opacity": 35,
        "duration": 10,
    },
    "safety-notice": {
        "id": "safety-notice",
        "name": "Safety Notice",
        "description": "Share an important safety reminder or instruction.",
        "title": "Safety Notice",
        "body": "Please follow posted instructions and use caution.",
        "footer": "",
        "background_color": "#7A4B00",
        "text_color": "#FFFFFF",
        "accent_color": "#FFD166",
        "alignment": "center",
        "overlay_opacity": 50,
        "duration": 12,
    },
    "emergency": {
        "id": "emergency",
        "name": "Emergency",
        "description": "Display a high-visibility urgent notice.",
        "title": "Important Notice",
        "body": "Follow staff instructions and remain calm.",
        "footer": "",
        "background_color": "#8B1E1E",
        "text_color": "#FFFFFF",
        "accent_color": "#FFD6D6",
        "alignment": "center",
        "overlay_opacity": 60,
        "duration": 15,
    },
}


def get_sign_templates() -> list[dict]:
    """Return all templates in display order."""
    return [
        deepcopy(SIGN_TEMPLATES[template_id])
        for template_id in SIGN_TEMPLATES
    ]


def get_sign_template(template_id: str) -> dict | None:
    """Return one template by ID, or None when it does not exist."""
    template = SIGN_TEMPLATES.get(template_id)

    if template is None:
        return None

    return deepcopy(template)
