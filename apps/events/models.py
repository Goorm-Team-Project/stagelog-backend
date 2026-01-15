from django.db import models
from django.utils import timezone

class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    kopis_id = models.CharField(unique=True, max_length=50)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    age = models.CharField(max_length=255, blank=True, null=True)
    poster = models.CharField(max_length=255, blank=True, null=True)
    time = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=255, blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    relate_url = models.CharField(max_length=500, blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True)
    group_name = models.CharField(max_length=100, null=True)

    class Meta:
        managed = True
        db_table = 'events'

class ArtistMapping(models.Model):
    mapping_id = models.AutoField(primary_key=True)
    raw_name = models.CharField(unique=True, max_length=100)
    stage_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'artist_mapping'