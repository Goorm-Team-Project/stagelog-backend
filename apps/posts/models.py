from django.db import models
from django.conf import settings

# Create your models here.

class Post(models.Model):
    post_id = models.BigAutoField(primary_key=True)

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        db_column="event_id",
        related_name="posts",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="posts",
    )

    #ERD: category ENUM (문자열 시작 -> 추후 choices로)
    category = models.CharField(max_length=30)

    title = models.CharField(max_length=255)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    views = models.IntegerField(default=0)

    class Meta:
        db_table = "posts"
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["user"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"Post({self.post_id}) {self.title}"