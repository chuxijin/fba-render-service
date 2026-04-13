#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import mimetypes
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from bs4 import BeautifulSoup


_SUPPORTED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'pdf'}


@dataclass
class _ImageDownloadContext:
    client: httpx.AsyncClient
    assets_dir: Path
    max_images: int
    downloaded_count: int = 0

    def can_download(self) -> bool:
        return self.downloaded_count < self.max_images

    def next_index(self) -> int:
        self.downloaded_count += 1
        return self.downloaded_count


def _guess_extension(*, source_url: str, content_type: str | None) -> str | None:
    if content_type:
        mapped = mimetypes.guess_extension(content_type.split(';', 1)[0].strip().lower())
        if mapped:
            ext = mapped.lstrip('.').lower()
            if ext == 'jpe':
                ext = 'jpg'
            if ext in _SUPPORTED_IMAGE_EXTS:
                return ext

    parsed = urlparse(source_url)
    path_ext = Path(parsed.path).suffix.lstrip('.').lower()
    if path_ext == 'jpe':
        path_ext = 'jpg'
    if path_ext in _SUPPORTED_IMAGE_EXTS:
        return path_ext

    return None


async def _download_image_to_assets(
    *,
    source_url: str,
    context: _ImageDownloadContext,
) -> str | None:
    if not context.can_download():
        return None

    try:
        response = await context.client.get(source_url)
        response.raise_for_status()
    except Exception:
        return None

    extension = _guess_extension(source_url=source_url, content_type=response.headers.get('content-type'))
    if extension is None:
        return None

    index = context.next_index()
    filename = f'image_{index:03d}.{extension}'
    target = context.assets_dir / filename
    target.write_bytes(response.content)
    return f'assets/{filename}'


async def _rewrite_html_images(html_text: str, *, context: _ImageDownloadContext) -> str:
    if '<img' not in html_text.lower():
        return html_text

    soup = BeautifulSoup(html_text, 'html.parser')
    changed = False
    for tag in soup.find_all('img'):
        src = (tag.get('src') or tag.get('_src') or '').strip()
        if not src:
            continue
        if src.startswith('assets/'):
            continue
        if not src.lower().startswith(('http://', 'https://')):
            continue

        localized = await _download_image_to_assets(source_url=src, context=context)
        if not localized:
            continue
        tag['src'] = localized
        changed = True

    return str(soup) if changed else html_text


async def _localize_value(value: object, *, context: _ImageDownloadContext) -> object:
    if isinstance(value, dict):
        result: dict = {}
        for key, item in value.items():
            result[key] = await _localize_value(item, context=context)
        return result

    if isinstance(value, list):
        return [await _localize_value(item, context=context) for item in value]

    if isinstance(value, str):
        return await _rewrite_html_images(value, context=context)

    return value


async def localize_context_images(
    *,
    context: dict,
    workspace: Path,
    timeout_seconds: float = 12.0,
    max_images: int = 40,
) -> dict:
    """
    Download remote HTML images into current job workspace and rewrite `img src`.

    The returned context is a deep-copied object and safe to pass to template render.
    """
    copied = deepcopy(context)
    assets_dir = workspace / 'assets'
    assets_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        download_context = _ImageDownloadContext(client=client, assets_dir=assets_dir, max_images=max_images)
        localized = await _localize_value(copied, context=download_context)

    if isinstance(localized, dict):
        return localized
    return copied
