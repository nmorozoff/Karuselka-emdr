#!/usr/bin/env python3
"""Instagram carousel competitor decompose: Apify + Kimi OCR (verbatim text for copywriter)."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

WORKSPACE = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def merge_env(workspace: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(load_env_file(workspace / "carusel-memory" / "analyze.env.local"))
    return env


def http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict | None = None,
    timeout: int = 120,
    retries: int = 3,
) -> object:
    body = None
    req_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = Request(url, data=body, headers=req_headers, method=method)
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"HTTP failed after {retries} attempts: {last_error}")


def fetch_bytes(url: str, timeout: int = 120, retries: int = 3) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 CaruselBot/1.0"})
            with urlopen(req, timeout=timeout) as resp:
                mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                return resp.read(), mime
        except Exception as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Download failed after {retries} attempts: {last_error}")


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/").split("/")
    for part in reversed(path):
        if part and part not in ("p", "reel", "reels"):
            return re.sub(r"[^a-zA-Z0-9_-]", "", part)[:40]
    return f"ig-{int(time.time())}"


def call_apify(source_url: str, env: dict[str, str]) -> dict:
    token = env.get("APIFY_TOKEN", "")
    if not token:
        raise RuntimeError("APIFY_TOKEN missing in analyze.env.local")
    actor = env.get("APIFY_INSTAGRAM_ACTOR_ID", "apify/instagram-api-scraper").replace("/", "~")
    timeout = int(env.get("APIFY_TIMEOUT_SECONDS", "60"))
    endpoint = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
    query = urlencode({"token": token})
    data = http_json(
        f"{endpoint}?{query}",
        method="POST",
        payload={"directUrls": [source_url], "resultsType": "posts", "resultsLimit": 1},
        timeout=max(30, min(timeout, 120)),
    )
    if not isinstance(data, list) or not data:
        raise RuntimeError("Apify returned no items")
    return data[0]


def collect_media_urls(item: dict) -> list[dict[str, str]]:
    urls: list[dict[str, str]] = []
    for image_url in item.get("images") or []:
        if image_url:
            urls.append({"url": image_url, "mime_type": "image/jpeg"})
    for child in item.get("childPosts") or []:
        if not isinstance(child, dict):
            continue
        if child.get("videoUrl"):
            urls.append({"url": child["videoUrl"], "mime_type": "video/mp4"})
        elif child.get("displayUrl"):
            urls.append({"url": child["displayUrl"], "mime_type": "image/jpeg"})
    if item.get("videoUrl"):
        urls.append({"url": item["videoUrl"], "mime_type": "video/mp4"})
    elif item.get("displayUrl") and not urls:
        urls.append({"url": item["displayUrl"], "mime_type": "image/jpeg"})
    # dedupe
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for entry in urls:
        if entry["url"] in seen:
            continue
        seen.add(entry["url"])
        unique.append(entry)
    return unique[:10]


def build_metadata_block(item: dict, source_url: str) -> str:
    comments = []
    for c in (item.get("topComments") or [])[:5]:
        if isinstance(c, dict) and c.get("text"):
            comments.append(str(c["text"]).strip())
    blocks = [
        f"Instagram URL: {item.get('url') or source_url}",
        f"Тип: {item.get('type', '')}",
        f"Автор: @{item.get('ownerUsername', '')} ({item.get('ownerFullName', '')})",
        f"Дата: {item.get('timestamp', '')}",
        "",
        "=== CAPTION (описание поста) — извлечь ДОСЛОВНО ===",
        item.get("caption") or "(пусто)",
    ]
    if comments:
        blocks.extend(["", "=== TOP COMMENTS (для контекста) ===", *comments])
    return "\n".join(blocks)


def build_kimi_prompt(metadata: str, slide_count: int) -> str:
    return f"""Ты OCR-аналитик Instagram-карусели. Задача — извлечь ВСЕ слова с картинок и из описания поста.

{metadata}

Для КАЖДОГО присланного изображения слайда (по порядку слева направо / как в карусели):
1. Перепиши ДОСЛОВНО весь видимый текст: заголовки, подзаголовки, буллеты, кнопки, мелкий текст, цифры.
2. Если текст нечитаем — напиши "[нечитаемо]" и опиши что видишь.
3. Не пересказывай — только точная транскрипция.

Также включи caption поста дословно в отдельное поле.

Верни ТОЛЬКО JSON без markdown:
{{
  "sourceType": "instagram-carousel",
  "slide_count_detected": число слайдов на картинках,
  "caption_verbatim": "полный текст описания поста",
  "slides": [
    {{"index": 1, "all_visible_text": "весь текст слайда одним блоком", "headline": "главный заголовок если есть", "body": "остальной текст"}}
  ],
  "full_text_combined": "caption + все слайды подряд, разделитель --- между блоками",
  "design_notes": "кратко: палитра, сетка, стиль, шрифты, layout",
  "warnings": []
}}

Ожидаемое число слайдов в карусели: {slide_count} (если на картинках другое — укажи в slide_count_detected).
Пиши по-русски. Сохраняй оригинальную орфографию и пунктуацию конкурента."""


def parse_json_content(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {"all_visible_text": raw.strip(), "headline": "", "body": ""}


def kimi_chat(api_key: str, model: str, content: list[dict], max_tokens: int) -> str:
    response = http_json(
        "https://api.moonshot.ai/v1/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {api_key}"},
        payload={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты точный OCR. Возвращай только текст с изображения.",
                },
                {"role": "user", "content": content},
            ],
            "max_tokens": max_tokens,
        },
        timeout=240,
    )
    return (((response or {}).get("choices") or [{}])[0].get("message") or {}).get("content", "")


def ocr_single_slide(
    asset: dict[str, str],
    slide_index: int,
    env: dict[str, str],
) -> dict:
    api_key = env.get("KIMI_API_KEY", "")
    model = env.get("KIMI_MODEL", "kimi-k2.5")
    prompt = (
        f"Слайд {slide_index} Instagram-карусели.\n"
        "Извлеки ДОСЛОВНО весь видимый текст: заголовки, подзаголовки, буллеты, кнопки, мелкий текст.\n"
        "Ответь только текстом со слайда, без комментариев. Сохрани переносы строк."
    )
    data_url = f"data:{asset['mime_type']};base64,{asset['data_b64']}"
    content = [
        {"type": "image_url", "image_url": {"url": data_url}},
        {"type": "text", "text": prompt},
    ]
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            raw = kimi_chat(api_key, model, content, max_tokens=2500)
            text = raw.strip()
            if text.startswith("{"):
                parsed = parse_json_content(text)
                parsed.setdefault("index", slide_index)
                parsed.setdefault("all_visible_text", parsed.get("all_visible_text") or text)
                return parsed
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            headline = lines[0] if lines else ""
            body = "\n".join(lines[1:]) if len(lines) > 1 else ""
            return {
                "index": slide_index,
                "all_visible_text": text,
                "headline": headline,
                "body": body,
            }
        except Exception as error:
            last_error = error
            time.sleep(2)
    raise RuntimeError(f"OCR slide {slide_index} failed: {last_error}")


def call_kimi(
    caption: str,
    image_assets: list[dict[str, str]],
    env: dict[str, str],
    target_slides: int = 6,
) -> dict:
    slides: list[dict] = []
    for i, asset in enumerate(image_assets, start=1):
        if not asset["mime_type"].startswith("image/"):
            continue
        print(f"Kimi OCR slide {i}/{len(image_assets)}...")
        slides.append(ocr_single_slide(asset, i, env))

    combined_parts = [f"=== CAPTION ===\n{caption or '(пусто)'}"]
    for slide in slides:
        combined_parts.append(
            f"=== SLIDE {slide.get('index', '?')} ===\n{slide.get('all_visible_text', '')}"
        )

    return {
        "sourceType": "instagram-carousel",
        "slide_count_detected": len(slides),
        "caption_verbatim": caption,
        "slides": slides,
        "full_text_combined": "\n\n---\n\n".join(combined_parts),
        "design_notes": (
            "Референс @life.practic: светлый editorial, крупная типографика, "
            "иллюстрации/метафоры, минимум текста на слайде. "
            f"У конкурента {len(slides)} слайдов — целевой формат: 6."
        ),
        "warnings": (
            [f"Конкурент: {len(slides)} слайдов, целевой формат: {target_slides}"]
            if len(slides) != target_slides
            else []
        ),
    }


def write_copywriter_handoff(out_dir: Path, source_url: str, item: dict, analysis: dict) -> Path:
    md_path = out_dir / "competitor-text-for-copywriter.md"
    lines = [
        "# Текст конкурентной карусели (verbatim → copywriter)",
        "",
        f"**Источник:** {source_url}",
        f"**Автор:** @{item.get('ownerUsername', '')}",
        f"**Слайдов (detected):** {analysis.get('slide_count_detected', '?')}",
        "",
        "## Описание поста (caption)",
        "",
        analysis.get("caption_verbatim") or item.get("caption") or "",
        "",
        "## Текст по слайдам",
        "",
    ]
    for slide in analysis.get("slides") or []:
        idx = slide.get("index", "?")
        lines.extend(
            [
                f"### Слайд {idx}",
                "",
                slide.get("all_visible_text") or "",
                "",
            ]
        )
    lines.extend(
        [
            "## Полный текст (combined)",
            "",
            analysis.get("full_text_combined") or "",
            "",
            "## Design notes (для designer / image-prompter)",
            "",
            analysis.get("design_notes") or "",
            "",
            "## Warnings",
            "",
            "\n".join(f"- {w}" for w in (analysis.get("warnings") or [])) or "none",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Decompose Instagram competitor carousel")
    parser.add_argument("url", help="Instagram post URL")
    parser.add_argument("--workspace", default=str(WORKSPACE))
    parser.add_argument("--slides", type=int, default=6, help="Expected slide count")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Skip Apify if apify-raw.json already exists in output dir",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    env = merge_env(workspace)
    slug = slug_from_url(args.url)
    out_dir = workspace / "carusel-memory" / "research" / "competitor-decompose" / slug
    media_dir = out_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    print(f"Apify: {args.url}")
    cached = out_dir / "apify-raw.json"
    if args.use_cache and cached.exists():
        print(f"Using cached Apify data: {cached}")
        item = json.loads(cached.read_text(encoding="utf-8"))
    else:
        item = call_apify(args.url, env)
        cached.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")

    metadata = build_metadata_block(item, args.url)
    (out_dir / "metadata.txt").write_text(metadata, encoding="utf-8")

    image_assets: list[dict[str, str]] = []
    for i, media in enumerate(collect_media_urls(item), start=1):
        if not media["mime_type"].startswith("image/"):
            print(f"Skip non-image media {i}: {media['mime_type']}")
            continue
        print(f"Download slide image {i}...")
        raw, mime = fetch_bytes(media["url"])
        ext = ".jpg" if "jpeg" in mime else ".png"
        (media_dir / f"slide-{i:02d}{ext}").write_bytes(raw)
        image_assets.append(
            {
                "mime_type": mime,
                "data_b64": base64.b64encode(raw).decode("ascii"),
                "source_url": media["url"],
            }
        )

    if not image_assets:
        raise RuntimeError("No carousel images downloaded from Apify")

    prompt = build_kimi_prompt(metadata, args.slides)
    print(f"Kimi OCR: {len(image_assets)} images...")
    analysis = call_kimi(item.get("caption") or "", image_assets, env, args.slides)

    result = {
        "source_url": args.url,
        "slug": slug,
        "apify": {
            "ownerUsername": item.get("ownerUsername"),
            "type": item.get("type"),
            "caption": item.get("caption"),
            "likesCount": item.get("likesCount"),
            "commentsCount": item.get("commentsCount"),
        },
        "media_files": [str(p) for p in sorted(media_dir.glob("*"))],
        "analysis": analysis,
    }
    json_path = out_dir / "decompose.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = write_copywriter_handoff(out_dir, args.url, item, analysis)
    print(f"OK: {json_path}")
    print(f"OK: {md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
