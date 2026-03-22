"""
WiiM Media Browser for presets and sources.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import StatusCodes
from ucapi.api_definitions import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
    Pagination,
    SearchOptions,
    SearchResults,
)

from uc_intg_wiim.device import WiiMDevice

_LOG = logging.getLogger(__name__)

MEDIA_TYPE_ROOT = "root"
MEDIA_TYPE_PRESETS = "presets"
MEDIA_TYPE_SOURCES = "sources"


async def browse(device: WiiMDevice, options: BrowseOptions) -> BrowseResults | StatusCodes:
    media_type = options.media_type or MEDIA_TYPE_ROOT

    if media_type == MEDIA_TYPE_ROOT or (options.media_id is None and options.media_type is None):
        return _browse_root(device)

    if media_type == MEDIA_TYPE_PRESETS:
        return _browse_presets(device, options)

    if media_type == MEDIA_TYPE_SOURCES:
        return _browse_sources(device)

    return StatusCodes.NOT_FOUND


async def search(device: WiiMDevice, options: SearchOptions) -> SearchResults | StatusCodes:
    query = options.query.lower()
    results: list[BrowseMediaItem] = []

    for i, preset in enumerate(device.presets, start=1):
        name = preset.get("name", f"Preset {i}")
        if query in name.lower():
            results.append(BrowseMediaItem(
                title=name,
                media_class=MediaClass.RADIO,
                media_type=MediaContentType.RADIO,
                media_id=f"preset_{i}",
                can_play=True,
                thumbnail=preset.get("image", None),
            ))

    for source_name in device.source_list:
        if query in source_name.lower():
            results.append(BrowseMediaItem(
                title=source_name,
                media_class=MediaClass.CHANNEL,
                media_type=MediaContentType.CHANNEL,
                media_id=f"source_{source_name}",
                can_play=True,
            ))

    return SearchResults(
        media=results,
        pagination=Pagination(page=1, limit=len(results), count=len(results)),
    )


def _browse_root(device: WiiMDevice) -> BrowseResults:
    items: list[BrowseMediaItem] = []

    if device.presets:
        items.append(BrowseMediaItem(
            title="Presets",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_PRESETS,
            media_id="presets",
            can_browse=True,
            subtitle=f"{len(device.presets)} presets",
        ))

    items.append(BrowseMediaItem(
        title="Sources",
        media_class=MediaClass.DIRECTORY,
        media_type=MEDIA_TYPE_SOURCES,
        media_id="sources",
        can_browse=True,
        subtitle=f"{len(device.source_list)} sources",
    ))

    return BrowseResults(
        media=BrowseMediaItem(
            title=device.name,
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_ROOT,
            media_id="root",
            can_browse=True,
            can_search=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


def _browse_presets(device: WiiMDevice, options: BrowseOptions) -> BrowseResults:
    page = options.paging.page if options.paging and options.paging.page else 1
    limit = options.paging.limit if options.paging and options.paging.limit else 20
    total = len(device.presets)

    start = (page - 1) * limit
    end = min(start + limit, total)

    items: list[BrowseMediaItem] = []
    for i, preset in enumerate(device.presets[start:end], start=start + 1):
        name = preset.get("name", f"Preset {i}")
        items.append(BrowseMediaItem(
            title=name,
            media_class=MediaClass.RADIO,
            media_type=MediaContentType.RADIO,
            media_id=f"preset_{i}",
            can_play=True,
            thumbnail=preset.get("image", None),
            subtitle=preset.get("source", ""),
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Presets",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_PRESETS,
            media_id="presets",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


def _browse_sources(device: WiiMDevice) -> BrowseResults:
    items: list[BrowseMediaItem] = []
    for source_name in device.source_list:
        items.append(BrowseMediaItem(
            title=source_name,
            media_class=MediaClass.CHANNEL,
            media_type=MediaContentType.CHANNEL,
            media_id=f"source_{source_name}",
            can_play=True,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Sources",
            media_class=MediaClass.DIRECTORY,
            media_type=MEDIA_TYPE_SOURCES,
            media_id="sources",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )
