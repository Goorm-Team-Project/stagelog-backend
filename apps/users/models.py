from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(
        self, 
        email, 
        nickname, 
        provider,
        provider_id,
        # [수정] 기본값 False 지정 (안 넣어도 에러 안 나게)
        is_email_sub=False, 
        is_events_notification_sub=False, 
        is_posts_notification_sub=False, 
        password=None, 
        **extra_fields
    ):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nickname=nickname,
            provider=provider,
            provider_id=provider_id,
            is_email_sub=is_email_sub,
            is_events_notification_sub=is_events_notification_sub,
            is_posts_notification_sub=is_posts_notification_sub,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password=None, **extra_fields):
        # [수정] 관리자 생성 시 필수 값 강제 설정
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        
        # [수정] 알림 설정값도 기본으로 넘겨줘야 함 (True/False 취향껏)
        extra_fields.setdefault('is_email_sub', False)
        extra_fields.setdefault('is_events_notification_sub', False)
        extra_fields.setdefault('is_posts_notification_sub', False)

        # 관리자 계정 생성
        return self.create_user(
            email=email,
            nickname=nickname,
            provider='admin',
            provider_id='admin',
            password=password,
            **extra_fields
        )

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    
    # --- [ERD 기반 필드] ---

    email = models.EmailField(unique=True, max_length=255)
    nickname = models.CharField(max_length=30)
    
    # OAuth 관련
    provider = models.CharField(max_length=255)
    provider_id = models.CharField(max_length=255)
    
    # 시간
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 알림 동의 여부
    is_email_sub = models.BooleanField(default=False)
    is_events_notification_sub = models.BooleanField(default=False)
    is_posts_notification_sub = models.BooleanField(default=False)
    
    # 권한 및 상태
    is_admin = models.BooleanField(default=False)
    
    # 게임 요소 (경험치, 레벨, 신뢰도)
    exp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    reliability_score = models.IntegerField(default=50)

    # [Django 필수 필드]
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname'] # 슈퍼유저 생성 시 닉네임도 물어봄

    @property
    def is_staff(self):
        return self.is_admin

    def __str__(self):
        return f"{self.nickname} ({self.email})"

    class Meta:
        db_table = 'users'

class RefreshToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refresh_tokens'

    def __str__(self):
        return f"{self.user.email}의 토큰"
