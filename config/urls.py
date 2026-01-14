'''
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
'''
from django.contrib import admin
from django.urls import path, include

from events import views as events_views
from posts import views as posts_views
from notifications import views as notifications_views
from common.utils import health_check

urlpatterns = [
    #admin은 Django 기본 구조상 prefix에 / 포함
    path('admin/', admin.site.urls),

    # Auth / Users (login 라우팅)
    path('api/auth/', include('users.urls')),
    path('api/users/', include('users.urls')),

    # Bookmarks 라우팅
    path('api/bookmarks/', include('bookmarks.urls')),

    # Events (events 라우팅)
    ## /api/events
    path('api/events', events_views.event_list, name='event_list'),
    ## /api/events/<id> ...
    path('api/events/', include('events.urls')),

    # Posts (posts 라우팅)
    path('api/posts', posts_views.posts_list, name='posts_list'),
    path('api/posts/', include('posts.urls')),

    # Comments 라우팅
    path('api/comments/', include('posts.comment_urls')),

    # Notifications 라우팅
    path('api/notifications', notifications_views.get_notification_list, name='get_notification_list'),
    path('api/notifications/', include('notifications.urls')),

    path('', health_check)
]