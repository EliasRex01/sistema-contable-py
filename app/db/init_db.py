"""Crea tablas (dev). En prod usar Alembic."""
from app.db.session import Base, engine
from app.db import models  # noqa

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("OK: tablas creadas")
