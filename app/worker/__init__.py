from app.worker.celery_app import celery_app  # noqa: F401  (entrypoint: celery -A app.worker.celery_app worker)
from app.worker import tasks  # noqa: F401  registra ocr.process_file
