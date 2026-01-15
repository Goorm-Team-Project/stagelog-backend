from django.db import models
from django.conf import settings

class Notification(models.Model):
    notification_id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_column='user_id'
    )

    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        db_column='post_id'
    )

    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        db_column='event_id'
    )
    
    relate_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Type(models.TextChoices):
        COMMENT = 'comment', 'Comment'
        EVENT = 'event', 'Event'
        POST_LIKE = 'post_like', 'Postlike'
        POST_DISLIKE = 'post_dislike', 'Postdislike'
        NOTICE = 'notice', 'Notice'

    type = models.CharField(
        max_length=20,
        choices = Type.choices,
        default = Type.COMMENT
    )

    is_read = models.BooleanField(default=False)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Noti[{self.notification_id}] User[{self.user_id}] : {self.message}"