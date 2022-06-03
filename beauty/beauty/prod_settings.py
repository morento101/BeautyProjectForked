from decouple import config

DATABASES = {
    'default': {
      'ENGINE': 'django.db.backends.postgresql_psycopg2',
      'HOST': config("DB_HOST"),
      'NAME': config("DB_NAME"),
      'USER': config("DB_USER"),
      'PASSWORD': config("DB_PASS"),
      'PORT': config("DB_PORT")
    }
}