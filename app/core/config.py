from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://contable:contable@localhost:5432/contable_py"
    REDIS_URL: str = "redis://localhost:6379/0"
    MASTER_KEY: str = "changeme"
    DNIT_TIMBRADO_URL: str = "https://marangatu.set.gov.py"
    CAPTCHA_PROVIDER: str = ""  # "2captcha" | "capsolver" | "" (manual/HITL)
    CAPTCHA_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
