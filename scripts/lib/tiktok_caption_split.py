"""Split Instagram caption → TikTok title + description."""

from __future__ import annotations

import re


def strip_hashtags(text: str) -> str:
    return re.sub(r"#[\w\u0400-\u04FF]+", "", text).replace("  ", " ").strip()


def truncate_title(text: str, max_len: int = 90) -> str:
    cleaned = strip_hashtags(text).strip()
    if len(cleaned) <= max_len:
        return cleaned
    slice_ = cleaned[:max_len]
    sp = slice_.rfind(" ")
    if sp > 40:
        return slice_[:sp].strip()
    return slice_.strip()


def split_caption(full_caption: str) -> tuple[str, str]:
    normalized = full_caption.replace("\r\n", "\n").strip()
    blocks = [b.strip() for b in re.split(r"\n{2,}", normalized) if b.strip()]
    if not blocks:
        return "", ""
    title = truncate_title(blocks[0])
    description = "\n\n".join(blocks[1:]).strip() if len(blocks) > 1 else normalized
    return title, description[:4000]
