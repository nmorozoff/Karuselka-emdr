#!/usr/bin/env python3
"""Generate 6 carousel slides via Runware GPT Image 2 (per-panel 1080×1350)."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts" / "lib"))


def load_env(workspace: Path) -> dict[str, str]:
    env = dict(os.environ)
    path = workspace / "carusel-memory" / "runware.env.local"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def file_to_data_uri(path: Path, max_side: int = 1280) -> str:
    suffix = path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(suffix, "jpeg")
    raw = path.read_bytes()
    try:
        from io import BytesIO

        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            scale = min(1.0, max_side / max(w, h))
            if scale < 1.0:
                img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=88, optimize=True)
            raw = buf.getvalue()
            mime = "jpeg"
    except Exception:
        pass
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def resolve_path(workspace: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else workspace / p


def flatten_verbatim(v: dict) -> str:
    lines: list[str] = []
    for key, value in v.items():
        if isinstance(value, list):
            lines.append(f"{key}: " + " | ".join(str(x) for x in value))
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def build_slide_prompt(cfg: dict, panel: dict, slide_num: int, total: int) -> str:
    style = cfg.get("style_lock", {})
    topic = cfg.get("topic", "")
    rules = cfg.get("typography_rules", {})
    verbatim = panel.get("verbatim_text", {})
    visual = panel.get("visual_only", "")

    style_bits = (
        f"VISUAL STYLE: editorial infographic carousel, cream matte background {style.get('background', '#f7f5ef')}, "
        f"accent {style.get('primary_accent', '#3d5c2e')}, {style.get('headline_font', 'Playfair Display')} headlines, "
        f"{style.get('body_font', 'Inter')} body, {style.get('mood', 'calm premium psychology')}."
    )
    contract = cfg.get("reference_contract", {})
    preserve = ", ".join(contract.get("preserve", [])[:6])
    change = ", ".join(contract.get("change", [])[:4])

    identity_note = ""
    if panel.get("role") in ("hook", "cta"):
        identity_note = (
            " IDENTITY: use reference photo — same woman Natalia Morozova, face/hair/skin from reference; "
            "ignore reference clothing if needed; warm professional psychologist."
        )

    text_block = flatten_verbatim(verbatim)
    return (
        f"{style_bits}\n"
        f"Reference @yura.muradyan layout — preserve: {preserve}. Change: {change}.{identity_note}\n"
        f"Single Instagram carousel panel {slide_num} of {total}, vertical 4:5, 1080×1350 px.\n"
        f"Role: {panel.get('role', '')}, archetype: {panel.get('archetype', '')}.\n"
        f"RENDER ONLY THIS RUSSIAN TEXT verbatim on the slide (no extra labels, no English UI words):\n"
        f"{text_block}\n"
        f"Visual direction: {visual}\n"
        f"Typography: exact text only; hierarchy headline > body > pill; safe margin 10-12%; Russian only; no emoji.\n"
        f"Topic: {topic}\n"
        f"Photorealistic editorial design, high contrast readable text, no watermark, no Instagram UI chrome."
    )


def pick_references(workspace: Path, cfg: dict, panel: dict) -> list[Path]:
    refs: list[Path] = []
    role_map = {
        "style_layout_anchor": None,
        "layout_hook": None,
        "layout_cta": None,
        "identity_primary": None,
        "identity_fallback": None,
    }
    for item in cfg.get("input_local_paths", []):
        role_map[item.get("role")] = resolve_path(workspace, item["path"])

    ref_slide = panel.get("reference_slide")
    if ref_slide:
        competitor = workspace / "carusel-memory/research/competitor-decompose/DbFiu0pCp2k/media"
        candidate = competitor / f"slide-{int(ref_slide):02d}.jpg"
        if candidate.exists():
            refs.append(candidate)

    if panel.get("role") in ("hook", "cta"):
        for key in ("identity_primary", "identity_fallback"):
            p = role_map.get(key)
            if p and p.exists():
                refs.append(p)
                break
    elif role_map.get("style_layout_anchor") and role_map["style_layout_anchor"].exists():
        refs.append(role_map["style_layout_anchor"])

    # dedupe preserve order
    seen: set[str] = set()
    unique: list[Path] = []
    for p in refs:
        s = str(p.resolve())
        if s in seen:
            continue
        seen.add(s)
        unique.append(p)
    return unique[:4]


def snap_dim(value: int) -> int:
    return max(16, (value + 15) // 16 * 16)


def crop_to_instagram(path: Path, target_w: int = 1080, target_h: int = 1350) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    with Image.open(path) as img:
        w, h = img.size
        if w == target_w and h == target_h:
            return
        left = max(0, (w - target_w) // 2)
        top = max(0, (h - target_h) // 2)
        crop = img.crop((left, top, left + target_w, top + target_h))
        crop.save(path, "PNG", optimize=True)


def run_inference(
    api_key: str,
    api_url: str,
    model: str,
    prompt: str,
    width: int,
    height: int,
    quality: str,
    references: list[Path],
) -> dict:
    task_uuid = str(uuid.uuid4())
    task: dict = {
        "taskType": "imageInference",
        "taskUUID": task_uuid,
        "model": model,
        "positivePrompt": prompt,
        "width": width,
        "height": height,
        "numberResults": 1,
        "outputType": "URL",
        "outputFormat": "PNG",
        "includeCost": True,
        "providerSettings": {"openai": {"quality": quality, "moderation": "auto"}},
    }
    if references:
        task["inputs"] = {"referenceImages": [file_to_data_uri(p) for p in references]}

    timeout = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "300"))
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            req = Request(
                api_url.rstrip("/"),
                data=json.dumps([task]).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data") or data.get("results") or []
            for item in items:
                if item.get("imageURL"):
                    return item
            errors = data.get("errors")
            raise RuntimeError(f"Runware failed: {json.dumps(errors or data, ensure_ascii=False)[:1500]}")
        except Exception as error:
            last_error = error
            import time

            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Runware failed after retries: {last_error}")


def download(url: str, dest: Path) -> None:
    import time

    last_error: Exception | None = None
    for attempt in range(5):
        try:
            req = Request(url, headers={"User-Agent": "carusel-runware/1.0"})
            with urlopen(req, timeout=180) as resp:
                dest.write_bytes(resp.read())
            return
        except Exception as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Download failed: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Runware carousel — 6 slides")
    parser.add_argument("--workspace", default=str(WORKSPACE))
    parser.add_argument(
        "--prompt-json",
        default="carusel-memory/design/CAROUSEL_IMAGE_PROMPT.json",
    )
    parser.add_argument("--slides", default="1,2,3,4,5,6", help="Comma-separated slide numbers")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    env = load_env(workspace)
    api_key = env.get("RUNWARE_API_KEY", "").strip()
    if not api_key:
        print("ERROR: RUNWARE_API_KEY missing", file=sys.stderr)
        return 1

    cfg_path = resolve_path(workspace, args.prompt_json)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    model = env.get("RUNWARE_GPT_IMAGE_MODEL", cfg.get("model", "openai:gpt-image@2"))
    api_url = env.get("RUNWARE_API_URL", "https://api.runware.ai/v1")
    quality = env.get("RUNWARE_IMAGE_QUALITY", cfg.get("quality", "medium"))
    width = snap_dim(int(env.get("RUNWARE_GPT_IMAGE_WIDTH", cfg.get("slide_width", 1080))))
    height = snap_dim(int(env.get("RUNWARE_GPT_IMAGE_HEIGHT", cfg.get("slide_height", 1350))))
    target_w = int(cfg.get("slide_width", 1080))
    target_h = int(cfg.get("slide_height", 1350))

    panels = {p["slide"]: p for p in cfg.get("panel_visual_brief", [])}
    slide_nums = [int(x.strip()) for x in args.slides.split(",") if x.strip()]

    out_dir = workspace / "carusel-memory" / "output" / "slides"
    master_dir = workspace / "carusel-memory" / "output" / "master"
    out_dir.mkdir(parents=True, exist_ok=True)
    master_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "mode": "per_slide_runware",
        "model": model,
        "quality": quality,
        "size": f"{width}x{height}",
        "slides": [],
        "total_cost_usd": 0.0,
    }

    for n in slide_nums:
        panel = panels.get(n)
        if not panel:
            print(f"WARN: no panel_visual_brief for slide {n}", file=sys.stderr)
            continue
        prompt = build_slide_prompt(cfg, panel, n, len(panels))
        refs = pick_references(workspace, cfg, panel)
        print(f"Generating slide {n}/6 refs={[p.name for p in refs]}...")
        result = run_inference(api_key, api_url, model, prompt, width, height, quality, refs)
        url = result.get("imageURL")
        if not url:
            raise RuntimeError(f"No imageURL for slide {n}: {result}")
        out_path = out_dir / f"slide-{n:02d}.png"
        if out_path.exists() and out_path.stat().st_size > 10000:
            print(f"Skip slide {n} — already exists")
            continue
        download(url, out_path)
        crop_to_instagram(out_path, target_w, target_h)
        # Обязательная очистка EXIF/AI-метаданных (как ai-carousel-natasha)
        from image_metadata_cleaner import clean_image_file, slide_title_from_index, load_slides_copy  # noqa: E402

        cleaner_env = load_env(workspace)
        cleaner_path = workspace / "carusel-memory" / "cleaner.env.local"
        if cleaner_path.exists():
            for line in cleaner_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cleaner_env[k.strip()] = v.strip()
        api_key = cleaner_env.get("AI_CLEANER_API_KEY", "")
        if not api_key:
            raise RuntimeError("AI_CLEANER_API_KEY missing — слайды без очистки метаданных не сохраняем")
        slides_copy = load_slides_copy(workspace)
        clean_image_file(
            out_path,
            api_key=api_key,
            api_url=cleaner_env.get("AI_CLEANER_API_URL", "https://mcp-kv.ru/ai-delete/api/clean"),
            title=slide_title_from_index(slides_copy, n),
            keywords="Instagram карусель, психология, EMDR, Наталья Морозова",
        )
        cost = float(result.get("cost") or 0)
        manifest["total_cost_usd"] += cost
        manifest["slides"].append(
            {
                "index": n,
                "path": str(out_path),
                "imageURL": url,
                "cost_usd": cost,
                "references": [str(p) for p in refs],
            }
        )
        print(f"OK slide-{n:02d}.png cost={cost}")

    manifest_path = workspace / "carusel-memory" / "output" / "runware-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")
    print(f"Total cost USD: {manifest['total_cost_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
