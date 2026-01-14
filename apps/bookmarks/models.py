from django.db import models
from django.conf import settings

class Bookmark(models.Model):
    #ERD: bookmark_id INT PK
    bookmark_id = models.BigAutoField(primary_key=True)

    #ERD: user_id FK
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="bookmarks",
    )

    #ERD: event_id FK (컬럼명 event_id -> 260107 ERD(latest) DB/ETL 수정 요청함)
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        db_column="event_id",
        related_name="bookmarks",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookmark"
        constraints = [
            models.UniqueConstraint(fields=["user", "event"], name="uq_bookmark_user_event")
        
        ]
    
    def __str__(self):
        return f"Bookmark(user_id={self.user_id}, event_id={self.event_id})"