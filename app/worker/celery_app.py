from celery import Celery
from app.core.config import settings

celery_app = Celery("contable", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(task_track_started=True, task_acks_late=True)
