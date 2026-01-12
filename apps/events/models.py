from django.db import models
from django.conf import settings
from django.utils import timezone

# Main Principles:
# 1. event_id는 KOPIS의 공연 ID와 동일하게 저장
# 2. 상세 조회는 이 키로 바로 조회되도록 설계

# Create your models here.

class Event(models.Model):
    # 내부 PK (ERD: event_id INT PK)
    event_id = models.BigAutoField(primary_key=True)
    # 외부 KOPIS ID (ERD: kopis_id VARCHAR NOT NULL)
    kopis_id  = models.CharField(max_length=50, unique=True)

    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, blank=True, null=True)

    start_date = models.DateField()
    end_date = models.DateField()

    venue = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)

    age = models.CharField(max_length=255, blank=True, null=True) # 관람 가능 연령 "만 7세 이상" 같은 문자열 가능
    price = models.CharField(max_length=255, blank=True, null=True) # "VIP석 150,000원" 같은 문자열 가능

    poster = models.URLField(max_length=255, blank=True, null=True)
    time = models.CharField(max_length=255, blank=True, null=True) # 금(10:00 - 12:00)" 같은 문자열 가능

    # 동기화/메타

    # 260112 수정 - upsert시 값 덮어쓰기 가능
    update_date = models.DateTimeField(default=timezone.now)
    relate_url = models.CharField(max_length=500, blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True, default="대중음악")

    class Meta:
        db_table = 'events'
        indexes = [
            models.Index(fields=["kopis_id"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"[{self.kopis_id}] {self.title}"

    class Meta:
        db_table = "events"
    
    def __str__(self):
        return f"Bookmark(user_id={self.user_id}, event_id={self.event_id})"
    