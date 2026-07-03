"""Application settings. Every variable is optional: with zero config the API
boots in demo mode (in-memory store, synthetic wearable data, local NLP fallback)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AI (optional — falls back to an explainable local lexicon)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Persistence (optional — falls back to in-memory store)
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Video generation: "mock" (ffmpeg slideshow, free) | "replicate"
    video_provider: str = "mock"
    replicate_api_token: str = ""
    replicate_model: str = ""

    # API
    cors_origins: str = "*"
    antifake_threshold: int = 60
    demo_user_id: str = "demo-user"
    demo_handle: str = "matiasbellidor"

    @property
    def demo_mode(self) -> bool:
        """True when Supabase is not configured. The whole pipeline still runs."""
        return not (self.supabase_url and self.supabase_service_key)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
