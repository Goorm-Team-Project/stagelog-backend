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
#정적파일경로설정
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

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