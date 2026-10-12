from sanic import Blueprint, HTTPResponse, empty, json
from sanic_ext import validate

from app.core.notifications import Notifications
from app.models.base import IDs

notification = Blueprint("notification", url_prefix="/notification")


@notification.get("/list")
async def list_notifications(_) -> HTTPResponse:
    """List the notifications.

    Args:
        _: Unused request.

    Returns:
        Response containing the requested data.
    """
    notifications = await Notifications.list()
    return json(
        [
            {
                "id": notification.id,
                "title": notification.title,
                "content": notification.content,
                "created_at": notification.created_at,
                "seen": notification.seen,
            }
            for notification in notifications
        ]
    )


@notification.post("/delete")
@validate(json=IDs)
async def delete_notifications(_, body: IDs) -> HTTPResponse:
    """Delete the notifications.

    Args:
        _: Unused request.
        body: Record IDs to act on.

    Returns:
        Empty response on success.
    """
    for id in body.ids:
        await Notifications.delete(int(id))
    return empty()


@notification.post("/clear")
async def clear_notifications(_) -> HTTPResponse:
    """Clear all notifications.

    Args:
        _: Unused request.

    Returns:
        Empty response on success.
    """
    await Notifications.delete()
    return empty()


@notification.post("/read")
async def read_notifications(_) -> HTTPResponse:
    """Mark all notifications as read.

    Args:
        _: Unused request.

    Returns:
        Empty response on success.
    """
    await Notifications.read()
    return empty()
