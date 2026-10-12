from enum import StrEnum, auto

from sanic import Request
from tortoise.expressions import Q

from app.core.constants import ENCODING
from app.core.exceptions import UnauthorizedException
from app.models.general import Notification
from app.models.user import UserInfo, UserRole
from app.utils import json


class NotificationTemplate(StrEnum):
    """The notification templates for Kaloscope application."""

    DOWNLOAD_FAILED = auto()
    DOWNLOAD_COMPLETED = auto()


class Notifications:
    """The notification manager."""

    @classmethod
    async def send(
        cls, template: NotificationTemplate, user_id: int | None = None, **kwargs
    ):
        """Send a notification with the given template and parameters.

        Args:
            template: Notification template to use.
            user_id: The ID of the user to send the notification to. `None` targets
                administrators.
            **kwargs: Parameters to fill in the template.
        """
        await Notification.create(
            user_id=user_id,
            role=UserRole.ADMIN if user_id is None else None,
            title=template.name,
            content=json.dumps(kwargs).decode(ENCODING),
        )

    @classmethod
    async def send_raw(cls, title: str, content: str, user_id: int | None = None):
        """Send a raw notification with the given title and content.

        Args:
            title: Title of the notification.
            content: Content of the notification.
            user_id: The ID of the user to send the notification to. `None` targets
                administrators.
        """
        await Notification.create(
            user_id=user_id,
            role=UserRole.ADMIN if user_id is None else None,
            title=title,
            content=content,
        )

    @classmethod
    def _filter(cls) -> Q:
        """Get filter for querying notifications based on the current user.

        Raises:
            UnauthorizedException: If the user is not logged in.

        Returns:
            Filter for querying notifications.
        """
        request = Request.get_current()
        if not hasattr(request.ctx, "user") or not request.ctx.user:
            raise UnauthorizedException

        user: UserInfo = request.ctx.user
        filter = Q(user_id=user.id)
        if user.role == UserRole.ADMIN:
            filter |= Q(role=UserRole.ADMIN)
        return filter

    @classmethod
    async def list(cls) -> list[Notification]:
        """List all notifications for the current user.

        Returns:
            List of notifications.
        """
        return (
            await Notification.filter(cls._filter()).order_by("-created_at").limit(200)
        )

    @classmethod
    async def read(cls, notification_id: int | None = None):
        """Mark one or all notifications as read for the current user.

        Args:
            notification_id: The ID of the notification to mark as read. `None` marks
                all notifications as read.
        """
        filter = cls._filter()
        if notification_id is not None:
            filter &= Q(id=notification_id)
        await Notification.filter(filter).update(seen=True)

    @classmethod
    async def delete(cls, notification_id: int | None = None):
        """Delete one or all notifications for the current user.

        Args:
            notification_id: The ID of the notification to delete. `None` deletes all
                matching notifications.
        """
        filter = cls._filter()
        if notification_id is not None:
            filter &= Q(id=notification_id)
        await Notification.filter(filter).delete()
