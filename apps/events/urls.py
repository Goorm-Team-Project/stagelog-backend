from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin", admin.site.urls),
    path("api/", include("event.urls")),
    #추후 users/auth/posts/comments도 동일한 방식으로 여기에 붙이기
]