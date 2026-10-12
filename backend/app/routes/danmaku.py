from sanic import Blueprint, HTTPResponse, empty, json
from sanic_ext import validate

from app.models.media import MediaResource
from app.services.danmaku import (
    AnimeConfirm,
    DanmakuQuery,
    DanmakuService,
    EpisodeConfirm,
)

danmaku = Blueprint("danmaku", url_prefix="/danmaku")


@danmaku.post("/match")
@validate(json=MediaResource)
async def match_danmakus(_, body: MediaResource) -> HTTPResponse:
    """Match overlay comments for the given media resource.

    Args:
        _: Unused request.
        body: Media source path.

    Returns:
        Response containing the requested data.
    """
    danmakus = await DanmakuService.match_danmakus(body.path)
    return json(danmakus.model_dump())


@danmaku.post("/delete")
@validate(json=MediaResource)
async def delete_danmakus(_, body: MediaResource) -> HTTPResponse:
    """Delete the locally cached overlay comments for the given media resource.

    Args:
        _: Unused request.
        body: Media source path.

    Returns:
        Empty response on success.
    """
    await DanmakuService.delete_danmakus(body.path)
    return empty()


@danmaku.post("/search")
@validate(json=DanmakuQuery)
async def search_episodes(_, body: DanmakuQuery) -> HTTPResponse:
    """Search for episodes matching the given title from the comment server.

    Args:
        _: Unused request.
        body: Media path and search title.

    Returns:
        Response containing the requested data.
    """
    episodes = await DanmakuService.search_episodes(body.path, body.title)
    return json([e.model_dump() for e in episodes])


@danmaku.post("/confirm")
@validate(json=EpisodeConfirm)
async def confirm_episode(_, body: EpisodeConfirm) -> HTTPResponse:
    """Confirm the episode match result for the given media resource.

    Args:
        _: Unused request.
        body: Media path and selected episode.

    Returns:
        Response containing the requested data.
    """
    danmakus = await DanmakuService.confirm_episode(body.path, body.metadata)
    return json(danmakus.model_dump())


@danmaku.post("/anime/search")
@validate(json=DanmakuQuery)
async def search_anime(_, body: DanmakuQuery) -> HTTPResponse:
    """Search anime for a media library item.

    Args:
        _: Unused request.
        body: Media path and search title.

    Returns:
        Response containing the requested data.
    """
    results = await DanmakuService.search_anime(body.path, body.title)
    return json([a.model_dump() for a in results])


@danmaku.post("/anime/confirm")
@validate(json=AnimeConfirm)
async def confirm_anime(_, body: AnimeConfirm) -> HTTPResponse:
    """Confirm an anime match for all files in a media library item.

    Args:
        _: Unused request.
        body: Media path and selected series.

    Returns:
        Response containing the requested data.
    """
    return json(await DanmakuService.confirm_anime(body.path, body.metadata))
