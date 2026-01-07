from django.db import models
from django.conf import settings

class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        db_column='user_id'
    )

    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='bookmarked_by',
        db_column='event_id'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookmark'
        unique_together = (('user', 'event'),)

    def __str__(self):
        return f"User[{self.user_id}] - Event[{self.event_id}]"