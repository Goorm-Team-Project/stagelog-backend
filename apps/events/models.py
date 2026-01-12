from django.db import models
from django.utils import timezone

class Event(models.Model):
    # 내부 PK (ERD: event_id INT PK)
    event_id = models.BigAutoField(primary_key=True)

    # 외부 KOPIS ID
    kopis_id = models.CharField(max_length=50, unique=True)

    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, blank=True, null=True)

    start_date = models.DateField()
    end_date = models.DateField()

    venue = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)

    age = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=255, blank=True, null=True)

    poster = models.URLField(max_length=255, blank=True, null=True)
    time = models.CharField(max_length=255, blank=True, null=True)

    # 동기화/메타
    update_date = models.DateTimeField(default=timezone.now)  # auto_now 제거 반영
    relate_url = models.CharField(max_length=500, blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True, default="대중음악")

    class Meta:
        db_table = "events"
        indexes = [
            models.Index(fields=["kopis_id"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"[{self.kopis_id}] {self.title}"
