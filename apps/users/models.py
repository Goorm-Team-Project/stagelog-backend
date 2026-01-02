from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, nickname, provider, provider_id, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nickname=nickname,
            provider=provider,
            provider_id=provider_id,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password=None, **extra_fields):
        # 슈퍼유저는 관리자 권한 필수
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        
        # 관리자 계정은 provider 정보가 딱히 없으니 임의로 설정
        return self.create_user(
            email=email,
            nickname=nickname,
            provider='local',      # 관리자는 로컬 생성
            provider_id='admin',   # 관리자 ID 식별자
            password=password,
            **extra_fields
        )

class User(AbstractBaseUser, PermissionsMixin):
    # --- [ERD 기반 필드 작성] -------------------------
    email = models.EmailField(unique=True, max_length=255)
    nickname = models.CharField(max_length=30)
    
    # OAuth 관련
    provider = models.CharField(max_length=255)
    provider_id = models.CharField(max_length=255) # 소셜 제공자의 고유 ID
    
    # 시간
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 알림 동의 여부 (기본값 True 설정)
    is_email_sub = models.BooleanField(default=True)
    is_events_notification_sub = models.BooleanField(default=True)
    is_posts_notification_sub = models.BooleanField(default=True)
    
    # 권한 및 상태
    is_admin = models.BooleanField(default=False) # ERD의 is_admin
    
    # 게임 요소 (경험치, 레벨, 신뢰도) - 초기값 0, 1 설정
    exp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    reliability_score = models.IntegerField(default=50)
    # ------------------------------------------------

    # [Django 필수 필드]
    is_active = models.BooleanField(default=True) # 로그인 가능 여부

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname'] # 슈퍼유저 생성 시 추가로 물어볼 필드

    # Django Admin 페이지 접속 권한을 is_admin 필드와 연결
    @property
    def is_staff(self):
        return self.is_admin

    def __str__(self):
        return f"{self.nickname} ({self.email})"

    class Meta:
        db_table = 'users'