from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "QuakePulse Backend"
    DATABASE_URL: str = "sqlite:///./quakepulse.db" # Can be switched to postgresql:// in .env

    # Target Bounding Box (Gulf of Suez)
    LAT_MIN: float = 22.0
    LAT_MAX: float = 32.0
    LON_MIN: float = 25.0
    LON_MAX: float = 36.0
    MIN_MAGNITUDE: float = 3.0

    MODEL_PATH: str = "data/model.json"

    class Config:
        env_file = ".env"

settings = Settings()
