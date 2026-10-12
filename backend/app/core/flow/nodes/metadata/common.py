"""Validate metadata candidates and resolve automatic publication targets."""

from typing import Literal
from uuid import UUID

from app.core.flow.context import MANUAL_KEY, RETVAL_KEY, Context
from app.core.media.common import ContentError
from app.core.media.metadata import METADATA_BYTES, ReadingMetadata, render_metadata
from app.models.media import LibType, MediaItem
from app.utils import json


async def publish_video(context: Context) -> None:
    """Publish automatic video candidates while keeping manual previews read-only.

    Args:
        context: Workflow context containing parsed candidates and target fields.

    Raises:
        ContentError: If automatic output is invalid. Existing NFO files and removed
            targets retain their successful-skip behavior.
    """
    from app.core.media.shelver import gen_nfo, nfo_context

    manual = context.bootparams.get(MANUAL_KEY)
    if not manual and not context.bootparams.get("nfo_type"):
        return
    candidates = context.get(RETVAL_KEY)
    if not isinstance(candidates, list) or any(
        not isinstance(candidate, dict) for candidate in candidates
    ):
        raise ContentError("invalid_metadata")
    if manual or not candidates:
        return
    item_id = context.bootparams.get("item_id")
    await gen_nfo(*nfo_context(context), item_id=item_id)


def parse_candidates(response: str, format: Literal["opf", "comicinfo"]) -> list[dict]:
    """Validate bounded JSONC candidates using the same rules as metadata saving.

    Args:
        response: Rendered response containing up to 100 candidate objects.
        format: Target metadata format for candidate round-trip validation.

    Returns:
        Normalized candidates, including an empty list for no search results.

    Raises:
        ContentError: If the response is oversized, malformed or unrepresentable.
    """
    if len(response.encode()) > METADATA_BYTES:
        raise ContentError("media_limit_exceeded")
    candidates = json.try_loads(response, with_comments=True)
    if not isinstance(candidates, list):
        raise ContentError("invalid_metadata")
    if len(candidates) > 100:
        raise ContentError("media_limit_exceeded")
    result = []
    for candidate in candidates:
        try:
            metadata = ReadingMetadata.model_validate_json(json.dumps(candidate))
        except (TypeError, ValueError) as error:
            raise ContentError("invalid_metadata") from error
        render_metadata(metadata, format, identifier=UUID(int=0))
        result.append(metadata.model_dump(mode="json", exclude_defaults=True))
    return result


async def reading_item(context: Context, lib_type: LibType) -> int | None:
    """Resolve the automatic target or validate a manual preview's library type.

    Args:
        context: Workflow context with server-selected source boot parameters.
        lib_type: Library type supported by the calling metadata node.

    Returns:
        Current item ID, or None for a manual preview without publication.

    Raises:
        ContentError: If the source is missing, invalid or belongs to another type.
    """
    params = context.bootparams
    if params.get(MANUAL_KEY) is True:
        if params.get("lib_type") != lib_type:
            raise ContentError("unsupported_media_format")
        return None
    id = params.get("item_id")
    if not isinstance(id, int) or isinstance(id, bool) or id <= 0:
        raise ContentError("invalid_metadata")
    item = await MediaItem.get_or_none(id=id).select_related("lib")
    if item is None:
        raise ContentError("not_found")
    if item.lib.lib_type != lib_type:
        raise ContentError("unsupported_media_format")
    return item.id
