import os

celery_broker_url = os.getenv("REDIS_BROKER_URL", default="redis://0.0.0.0:6379/1")
celery_result_backend = os.getenv("REDIS_RESULT_BACKEND", default="redis://0.0.0.0:6379/1")
celery_broker_connection_retry_on_startup = True
celery_timezone = "Europe/Moscow"
celery_enable_utc = False
celery_task_time_limit = 43200