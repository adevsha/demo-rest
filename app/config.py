import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+asyncmy://demo:demo@localhost:3306/demo_rest",
    )
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/demo_rest")
    MONGO_DB: str = os.getenv("MONGO_DB", "demo_rest")
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "demo-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30


settings = Settings()
