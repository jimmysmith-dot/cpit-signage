"""Template pack discovery and validation for CPIT Signage Studio."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = PROJECT_ROOT / "packs"

SUPPORTED_TEMPLATE_FIELDS = {
    "id", "name", "description", "title", "body", "footer",
    "background_color", "text_color", "accent_color", "alignment",
    "overlay_opacity", "duration", "background_asset",
}

REQUIRED_TEMPLATE_FIELDS = {"id", "name"}
REQUIRED_MANIFEST_FIELDS = {"id", "name", "version"}


class TemplatePackError(ValueError):
    """Raised when an installed template pack is invalid."""


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise TemplatePackError(
            f"Missing required pack file: {path.name}"
        ) from error
    except json.JSONDecodeError as error:
        raise TemplatePackError(
            f"Invalid JSON in {path.name}: {error}"
        ) from error


def _normalize_pack_id(value: str) -> str:
    pack_id = str(value).strip().lower()

    if not pack_id:
        raise TemplatePackError("Pack ID cannot be empty.")

    if any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-_"
        for character in pack_id
    ):
        raise TemplatePackError(
            "Pack ID may contain only lowercase letters, "
            "numbers, hyphens, and underscores."
        )

    return pack_id


def _validate_manifest(data, pack_directory: Path) -> dict:
    if not isinstance(data, dict):
        raise TemplatePackError("manifest.json must contain an object.")

    missing = REQUIRED_MANIFEST_FIELDS - data.keys()

    if missing:
        raise TemplatePackError(
            "manifest.json is missing required field(s): "
            + ", ".join(sorted(missing))
        )

    pack_id = _normalize_pack_id(data["id"])

    if pack_id != pack_directory.name:
        raise TemplatePackError(
            f"Manifest ID '{pack_id}' does not match "
            f"folder name '{pack_directory.name}'."
        )

    return {
        "id": pack_id,
        "name": str(data["name"]).strip(),
        "version": str(data["version"]).strip(),
        "description": str(data.get("description", "")).strip(),
        "author": str(data.get("author", "")).strip(),
    }


def _validate_template(template, manifest: dict) -> dict:
    if not isinstance(template, dict):
        raise TemplatePackError(
            f"Templates for {manifest['id']} must be JSON objects."
        )

    missing = REQUIRED_TEMPLATE_FIELDS - template.keys()

    if missing:
        raise TemplatePackError(
            "Template is missing required field(s): "
            + ", ".join(sorted(missing))
        )

    local_id = str(template["id"]).strip().lower()

    if not local_id:
        raise TemplatePackError("Template ID cannot be empty.")

    if ":" in local_id:
        raise TemplatePackError(
            "Pack template IDs must not contain ':'. "
            "The namespace is added automatically."
        )

    normalized = {
        key: deepcopy(value)
        for key, value in template.items()
        if key in SUPPORTED_TEMPLATE_FIELDS
    }

    normalized["id"] = f"{manifest['id']}:{local_id}"
    normalized["pack_id"] = manifest["id"]
    normalized["pack_name"] = manifest["name"]
    normalized["pack_version"] = manifest["version"]
    normalized["source"] = "pack"

    normalized.setdefault("description", "")
    normalized.setdefault("title", "")
    normalized.setdefault("body", "")
    normalized.setdefault("footer", "")
    normalized.setdefault("background_color", "#153A5B")
    normalized.setdefault("text_color", "#FFFFFF")
    normalized.setdefault("accent_color", "#75B9E6")
    normalized.setdefault("alignment", "center")
    normalized.setdefault("overlay_opacity", 35)
    normalized.setdefault("duration", 10)

    background_asset = str(
        normalized.get("background_asset", "")
    ).strip()

    if background_asset:
        background_path = (
            PACKS_DIR
            / manifest["id"]
            / "backgrounds"
            / background_asset
        )

        if (
            Path(background_asset).name != background_asset
            or not background_path.is_file()
        ):
            raise TemplatePackError(
                f"Template '{normalized['id']}' references a "
                "missing or invalid background asset."
            )

        normalized["background_asset"] = background_asset
        normalized["background_pack_asset"] = (
            f"{manifest['id']}:{background_asset}"
        )
        normalized["background_asset_url"] = (
            f"/api/template-packs/{manifest['id']}"
            f"/backgrounds/{background_asset}"
        )
    else:
        normalized["background_asset"] = ""
        normalized["background_pack_asset"] = ""
        normalized["background_asset_url"] = ""

    if normalized["alignment"] not in {"left", "center", "right"}:
        raise TemplatePackError(
            f"Template '{normalized['id']}' has an invalid alignment."
        )

    try:
        normalized["overlay_opacity"] = int(
            normalized["overlay_opacity"]
        )
        normalized["duration"] = int(normalized["duration"])
    except (TypeError, ValueError) as error:
        raise TemplatePackError(
            f"Template '{normalized['id']}' has invalid numeric fields."
        ) from error

    return normalized


def discover_template_packs() -> list[dict]:
    """Return metadata for valid installed packs."""
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    packs = []

    for pack_directory in sorted(
        (
            path
            for path in PACKS_DIR.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ),
        key=lambda path: path.name.lower(),
    ):
        try:
            manifest = _validate_manifest(
                _read_json(pack_directory / "manifest.json"),
                pack_directory,
            )
        except TemplatePackError:
            continue

        packs.append(manifest)

    return packs


def load_template_pack(pack_directory: Path) -> list[dict]:
    """Load and validate one installed template pack."""
    manifest = _validate_manifest(
        _read_json(pack_directory / "manifest.json"),
        pack_directory,
    )

    templates_data = _read_json(
        pack_directory / "templates.json"
    )

    if not isinstance(templates_data, list):
        raise TemplatePackError(
            "templates.json must contain an array of templates."
        )

    return [
        _validate_template(template, manifest)
        for template in templates_data
    ]


def get_pack_templates() -> list[dict]:
    """Return templates from all valid installed packs."""
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    templates = []

    for pack_directory in sorted(
        (
            path
            for path in PACKS_DIR.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ),
        key=lambda path: path.name.lower(),
    ):
        try:
            templates.extend(load_template_pack(pack_directory))
        except TemplatePackError:
            continue

    return templates


def get_pack_template(template_id: str) -> dict | None:
    """Return one namespaced pack template by ID."""
    normalized_id = str(template_id).strip()

    if ":" not in normalized_id:
        return None

    pack_id, _ = normalized_id.split(":", 1)
    pack_directory = PACKS_DIR / pack_id

    if not pack_directory.is_dir():
        return None

    try:
        templates = load_template_pack(pack_directory)
    except TemplatePackError:
        return None

    for template in templates:
        if template["id"] == normalized_id:
            return deepcopy(template)

    return None


def get_pack_background_path(
    pack_id: str,
    filename: str,
) -> Path | None:
    """Resolve one safe bundled background asset."""
    normalized_pack_id = _normalize_pack_id(pack_id)
    safe_filename = Path(str(filename)).name

    if safe_filename != str(filename) or not safe_filename:
        return None

    pack_directory = PACKS_DIR / normalized_pack_id

    if not pack_directory.is_dir():
        return None

    try:
        _validate_manifest(
            _read_json(pack_directory / "manifest.json"),
            pack_directory,
        )
    except TemplatePackError:
        return None

    path = pack_directory / "backgrounds" / safe_filename

    if not path.is_file():
        return None

    return path

def get_installed_template_packs():
    """Return metadata for installed and valid template packs."""
    result = []
    for manifest in discover_template_packs():
        item = dict(manifest)
        try:
            item["template_count"] = len(load_template_pack(PACKS_DIR / manifest["id"]))
            item["valid"] = True
            item["error"] = ""
        except TemplatePackError as error:
            item["template_count"] = 0
            item["valid"] = False
            item["error"] = str(error)
        result.append(item)
    return result


def install_template_pack_zip(zip_path: Path):
    """Safely validate and install a template-pack ZIP."""
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        archive = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile) as error:
        raise TemplatePackError("The uploaded file is not a valid ZIP archive.") from error

    with archive:
        files = [m for m in archive.infolist() if not m.is_dir()]
        if not files:
            raise TemplatePackError("The template pack ZIP is empty.")
        if len(files) > 500 or sum(m.file_size for m in files) > 100 * 1024 * 1024:
            raise TemplatePackError("The template pack ZIP exceeds installation limits.")

        with tempfile.TemporaryDirectory(prefix="cpit-pack-") as temp:
            root = Path(temp).resolve()
            for member in files:
                relative = Path(member.filename)
                if relative.is_absolute() or ".." in relative.parts:
                    raise TemplatePackError("The ZIP contains an unsafe file path.")
                destination = (root / relative).resolve()
                if root not in destination.parents:
                    raise TemplatePackError("The ZIP contains an unsafe file path.")
            archive.extractall(root)

            roots = [p for p in root.iterdir() if p.name != "__MACOSX"]
            source = roots[0] if len(roots) == 1 and roots[0].is_dir() else root

            manifest_data = _read_json(source / "manifest.json")
            pack_id = _normalize_pack_id(manifest_data.get("id", ""))
            staging = root / ".validated" / pack_id
            staging.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, staging)
            manifest = _validate_manifest(_read_json(staging / "manifest.json"), staging)

            templates_data = _read_json(staging / "templates.json")
            if not isinstance(templates_data, list):
                raise TemplatePackError("templates.json must contain an array of templates.")

            for template in templates_data:
                if not isinstance(template, dict):
                    raise TemplatePackError("Templates must be JSON objects.")
                missing = REQUIRED_TEMPLATE_FIELDS - template.keys()
                if missing:
                    raise TemplatePackError(
                        "Template is missing required field(s): " + ", ".join(sorted(missing))
                    )
                background = str(template.get("background_asset", "")).strip()
                if background:
                    if Path(background).name != background:
                        raise TemplatePackError("A template contains an invalid background asset.")
                    if not (staging / "backgrounds" / background).is_file():
                        raise TemplatePackError(
                            f"Template '{template.get('id', '')}' references a missing background asset."
                        )

            target = PACKS_DIR / pack_id
            if target.exists():
                raise TemplatePackError(f"Template pack '{pack_id}' is already installed.")
            shutil.copytree(staging, target)

            # Full installed validation uses the existing production loader.
            templates = load_template_pack(target)
            result = dict(manifest)
            result["template_count"] = len(templates)
            result["valid"] = True
            return result


def uninstall_template_pack(pack_id: str):
    """Remove one installed optional template pack."""
    normalized = _normalize_pack_id(pack_id)
    target = PACKS_DIR / normalized
    if not target.is_dir():
        raise TemplatePackError("Template pack is not installed.")
    manifest = _validate_manifest(_read_json(target / "manifest.json"), target)
    shutil.rmtree(target)
    return manifest
