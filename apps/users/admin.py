from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 가장 기본적인 등록 방법
admin.site.register(User)

# 만약 더 상세한 기능을 원하시면 아래처럼 사용해도 됩니다.
# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     model = User
#     list_display = ['email', 'nickname', 'is_admin', 'is_staff']