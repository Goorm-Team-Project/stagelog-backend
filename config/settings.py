from pathlib import Path
import os
import environ
import sys

# 1. 환경변수
env = environ.Env(
    DEBUG=(bool, False)
)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
db_mode = env('DB_MODE', default='sqlite')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

KAKAO_REST_API_KEY = env('KAKAO_REST_API_KEY')
KAKAO_REDIRECT_URI = env('KAKAO_REDIRECT_URI')
KAKAO_ACCESS_TOKEN_CLIENT_SECRET = env('KAKAO_ACCESS_TOKEN_CLIENT_SECRET')
NAVER_REST_API_KEY = env('NAVER_REST_API_KEY')
NAVER_REDIRECT_URI = env('NAVER_REDIRECT_URI')
NAVER_ACCESS_TOKEN_CLIENT_SECRET = env('NAVER_ACCESS_TOKEN_CLIENT_SECRET')
GOOGLE_REST_API_KEY = env('GOOGLE_REST_API_KEY')
GOOGLE_ACCESS_TOKEN_CLIENT_SECRET = env('GOOGLE_ACCESS_TOKEN_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = env('GOOGLE_REDIRECT_URI')

# 2. 앱 설정 (DRF, SimpleJWT 제거)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party
    'corsheaders', # CORS는 필수

    # Local Apps
    'users',
    'events',
    'posts',
    'bookmarks',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # 최상단
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'config.wsgi.application'

# 3. 데이터베이스 (MariaDB)
if db_mode == 'sqlite':
    DATABASES = {
        'default' : {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'stagelog',
            'USER': 'admin',
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', ''),
            'PORT': '3306',
            'OPTIONS': {
                'ssl': {
                    'ca': None,#os.path.join(BASE_DIR, 'certs/global-bundle.pem'),
                },
                'ssl_mode': 'REQUIRED',
                'charset': 'utf8mb4',
            },
        }
    }


# 4. 커스텀 유저 모델
AUTH_USER_MODEL = 'users.User' 

# 5. 비밀번호 검증
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 6. 언어 및 시간
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# 7. Trailing Slash 제거
APPEND_SLASH = False

# 8. CORS 설정
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# 9. JWT 설정 (수동 구현용 변수)
# SimpleJWT 설정은 제거하고, 직접 구현 시 사용할 알고리즘/만료시간만 환경변수나 상수로 관리 추천
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = env.int('JWT_EXP_DELTA_SECONDS', default= 60 * 30)

# 10. 정적파일경로설정
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 11. ALB사용 시 리다이렉션 오류 방지
# ALB가 전달해준 원래 호스트 정보를 신뢰합니다.
USE_X_FORWARDED_HOST = True

# AWS SES 설정
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID_WOOSUPAR')
AWS_SECRET_ACCESS_KEY_WOOSUPAR = env('AWS_SECRET_ACCESS_KEY_WOOSUPAR')
AWS_SES_REGION_NAME = env('AWS_SES_REGION_NAME')
AWS_SES_REGION_ENDPOINT = 'email.ap-northeast-2.amazonaws.com'

SES_DEFAULT_FROM_EMAIL = env('SES_DEFAULT_FROM_EMAIL')

# 10. AWS S3 (Presigned Upload)
AWS_REGION = env("AWS_REGION", default=env("AWS_DEFAULT_REGION", default="ap-northeast-2"))

# 10-1. bucket 키는 여러 이름 fallback 지원
S3_UPLOAD_BUCKET = env(
    "S3_UPLOAD_BUCKET",
    default=env("AWS_STORAGE_BUCKET_NAME", default=env("S3_BUCKET", default="")),
)

S3_UPLOAD_PREFIX = env("S3_UPLOAD_PREFIX", default="uploads/")
S3_PRESIGN_EXPIRES = env.int("S3_PRESIGN_EXPIRES", default=300)

# <-- (추후 커스텀 도메인/CloudFront 대응용, 여기에 base URL 지정) -->
# S3_PUBLIC_BASE_URL = env("S3_PUBLIC_BASE_URL", default=None)