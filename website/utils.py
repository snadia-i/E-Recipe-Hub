from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from flask import current_app, url_for
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def clean_text(value: str | None, *, max_length: int | None = None) -> str:
    text = (value or "").strip()
    if max_length is not None:
        text = text[:max_length]
    return text


def parse_positive_int(value: str | int | None, field_name: str) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number.") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return parsed


def allowed_image(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def _blob_is_configured() -> bool:
    return bool(
        os.environ.get("BLOB_READ_WRITE_TOKEN")
        or (os.environ.get("BLOB_STORE_ID") and os.environ.get("VERCEL_OIDC_TOKEN"))
    )


def _upload_to_vercel_blob(file: FileStorage, filename: str) -> str:
    try:
        from vercel.blob import BlobClient
    except ImportError as exc:
        raise ValueError("Vercel Blob support is not installed. Install requirements.txt.") from exc

    file.stream.seek(0)
    body = file.stream.read()
    client = BlobClient(token=os.environ.get("BLOB_READ_WRITE_TOKEN") or None)
    try:
        result = client.put(
            f"recipe-hub/uploads/{filename}",
            body,
            access="public",
            content_type=file.mimetype or "application/octet-stream",
            add_random_suffix=True,
        )
        return result.url
    finally:
        client.close()


def save_image(file: FileStorage | None) -> str | None:
    if file is None or not file.filename:
        return None
    if not allowed_image(file.filename):
        raise ValueError("Only PNG, JPG, JPEG, GIF, and WEBP images are allowed.")

    safe_name = secure_filename(file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"

    if _blob_is_configured():
        return _upload_to_vercel_blob(file, filename)

    if current_app.config.get("IS_VERCEL"):
        raise ValueError(
            "Image uploads are not configured. Connect a public Vercel Blob store first."
        )

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    file.save(upload_folder / filename)
    return url_for("static", filename=f"uploads/{filename}")


def row_to_dict(row):
    return dict(row) if row is not None else None
