"""EXIF/AI metadata cleanup via mcp-kv ai-delete API (same as ai-carousel-natasha)."""

from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BRAND_DESCRIPTION = "Психолог Наталья Морозова EMDR терапевт"
DEFAULT_API_URL = "https://mcp-kv.ru/ai-delete/api/clean"


def build_cleaner_seo_fields(
    title: str,
    keywords: str = "",
    description: str = "",
) -> dict[str, str]:
    clean_title = (title or "").strip() or "Instagram carousel"
    clean_keywords = (keywords or "").strip() or "Instagram карусель, психология, EMDR"
    clean_description = (description or "").strip()
    if not clean_description:
        if clean_title and clean_title != "Instagram carousel":
            clean_description = f"{clean_title}. {BRAND_DESCRIPTION}. Instagram карусель."
        else:
            clean_description = f"{BRAND_DESCRIPTION}. Instagram карусель."

    return {
        "title": clean_title[:2000],
        "description": clean_description[:2000],
        "keywords": clean_keywords[:2000],
        "comment": clean_keywords[:2000],
        "author": "@nataliamorozova.psy",
        "copyright": "© 2026 Наталья Морозова. All Rights Reserved",
        "software": "Adobe Lightroom Classic 14.2",
    }


def _normalize_mime_type(mime_type: str) -> str:
    cleaned = (mime_type or "image/png").split(";")[0].strip().lower()
    if cleaned in ("image/jpg", "image/pjpeg"):
        return "image/jpeg"
    if cleaned in ("image/png", "image/jpeg", "image/webp"):
        return cleaned
    return "image/png"


def _build_multipart_form(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = f"----Carusel{uuid.uuid4().hex}"
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")
    for name, (filename, content, mime) in files.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(),
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        body.extend(content)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: int = 120,
) -> tuple[bytes, str]:
    req = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.read(), response.headers.get("Content-Type", "application/octet-stream")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"{method} {url} failed HTTP {error.code}: {detail}") from error


def _parse_cleaner_response(raw: bytes, content_type: str, fallback_mime: str) -> tuple[bytes, str]:
    normalized = (content_type or "").split(";")[0].strip().lower()
    if normalized.startswith("image/"):
        return raw, _normalize_mime_type(normalized)

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        if len(raw) > 1000 and raw[:2] == b"\xff\xd8":
            return raw, "image/jpeg"
        raise RuntimeError("AI Cleaner вернул нераспознанный ответ")

    if not isinstance(parsed, dict):
        raise RuntimeError("AI Cleaner вернул нераспознанный ответ")

    if parsed.get("image_base64"):
        mime = _normalize_mime_type(str(parsed.get("mime_type") or fallback_mime))
        return base64.b64decode(str(parsed["image_base64"])), mime

    download_url = parsed.get("download_url")
    if isinstance(download_url, str) and download_url.strip():
        image_bytes, remote_type = _http_request(download_url.strip(), timeout=90)
        return image_bytes, _normalize_mime_type(remote_type or fallback_mime)

    raise RuntimeError("AI Cleaner не вернул очищенное изображение")


def clean_image_bytes(
    image_bytes: bytes,
    mime_type: str,
    *,
    api_key: str,
    api_url: str = DEFAULT_API_URL,
    title: str = "",
    keywords: str = "",
    description: str = "",
    timeout: int = 120,
) -> tuple[bytes, str]:
    if not api_key.strip():
        raise RuntimeError("AI_CLEANER_API_KEY missing — metadata clean обязателен перед публикацией")

    seo = build_cleaner_seo_fields(title, keywords, description)
    resolved_mime = _normalize_mime_type(mime_type)
    ext = "jpeg" if resolved_mime == "image/jpeg" else "png"
    form_fields = {
        "title": seo["title"],
        "author": seo["author"],
        "copyright": seo["copyright"],
        "software": seo["software"],
        "description": seo["description"],
        "keywords": seo["keywords"],
        "comment": seo["comment"],
    }
    form_files = {"file": (f"slide.{ext}", image_bytes, resolved_mime)}
    body, content_type = _build_multipart_form(form_fields, form_files)
    cleaned_raw, response_type = _http_request(
        api_url.rstrip("/"),
        method="POST",
        headers={"X-API-Key": api_key, "Content-Type": content_type},
        body=body,
        timeout=timeout,
    )
    return _parse_cleaner_response(cleaned_raw, response_type, resolved_mime)


def clean_image_file(
    path: Path,
    *,
    api_key: str,
    api_url: str = DEFAULT_API_URL,
    title: str = "",
    keywords: str = "",
    description: str = "",
    timeout: int = 120,
) -> dict[str, str | int]:
    """Clean file in-place. Returns report dict."""
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    cleaned, cleaned_mime = clean_image_bytes(
        raw,
        mime,
        api_key=api_key,
        api_url=api_url,
        title=title,
        keywords=keywords,
        description=description,
        timeout=timeout,
    )
    if cleaned_mime == "image/jpeg" and suffix not in (".jpg", ".jpeg"):
        out_path = path.with_suffix(".jpg")
        if out_path != path and path.exists():
            path.unlink()
        path = out_path
    path.write_bytes(cleaned)
    return {
        "path": str(path),
        "bytes_in": len(raw),
        "bytes_out": len(cleaned),
        "mime": cleaned_mime,
        "title": title[:120],
    }


def slide_title_from_index(slides_copy: dict[int, dict], index: int) -> str:
    slide = slides_copy.get(index) or {}
    headline = (slide.get("headline") or slide.get("title") or "").strip()
    if headline:
        return headline
    body = (slide.get("body") or slide.get("content") or "").strip()
    return body[:80] if body else f"Слайд {index}"


def load_slides_copy(workspace: Path) -> dict[int, dict]:
    path = workspace / "carusel-memory/design/CAROUSEL_SLIDE_COPY.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for slide in data.get("slides") or []:
        if "index" in slide:
            out[int(slide["index"])] = slide
    return out


def clean_slides_directory(
    slides_dir: Path,
    *,
    api_key: str,
    api_url: str = DEFAULT_API_URL,
    slides_copy: dict[int, dict] | None = None,
    pattern: str = "slide-*.png",
) -> list[dict[str, str | int]]:
    slides_dir = Path(slides_dir)
    reports: list[dict[str, str | int]] = []
    files = sorted(slides_dir.glob(pattern)) + sorted(slides_dir.glob("slide-*.jpg"))
    seen: set[str] = set()
    for fp in files:
        key = str(fp.resolve())
        if key in seen:
            continue
        seen.add(key)
        index = 0
        stem = fp.stem
        if stem.startswith("slide-"):
            try:
                index = int(stem.split("-", 1)[1])
            except ValueError:
                index = 0
        title = slide_title_from_index(slides_copy or {}, index) if index else fp.stem
        reports.append(
            clean_image_file(
                fp,
                api_key=api_key,
                api_url=api_url,
                title=title,
                keywords="Instagram карусель, психология, EMDR, Наталья Морозова",
            )
        )
    if not reports:
        raise RuntimeError(f"Нет слайдов для очистки в {slides_dir}")
    return reports
