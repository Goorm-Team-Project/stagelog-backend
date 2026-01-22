from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 가장 기본적인 등록 방법
admin.site.register(User)