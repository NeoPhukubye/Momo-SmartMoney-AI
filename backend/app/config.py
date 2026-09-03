from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "MoMo SmartMoney AI"
    app_env: str = "development"
    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite+aiosqlite:///./smartmoney.db"

    # Google Gemini AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # MTN MoMo
    momo_api_base_url: str = "https://proxy.momoapi.mtn.com/collection"
    momo_target_environment: str = "mtnsouthafrica"
    momo_collection_primary_key: str = ""
    momo_disbursement_primary_key: str = ""
    momo_api_user: str = ""
    momo_api_key: str = ""
    momo_environment: str = "mtnsouthafrica"

    # Africa's Talking
    at_username: str = "sandbox"
    at_api_key: str = ""

    # CORS
    cors_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "https://neophukubye.github.io,https://momo-smartmoney-ai.onrender.com"
    )

    # JWT
    access_token_expire_minutes: int = 60 * 24

    # Rate limiting
    rate_limit_per_minute: int = 30

    # Render
    render: bool = False
    port: int = 8000

    # Stokvel MTN enforcement
    # Comma-separated list of phone-number prefixes that identify MTN subscribers.
    # Numbers are normalized to digits and matched against these prefixes after the
    # country code (default country code: 27 = South Africa).
    mtn_default_country_code: str = "27"
    mtn_prefixes: str = "083,081,082,084,078,079"

    # Google Wallet ("Add to Google Wallet")
    # issuer_id: ~20-digit number from the Google Pay & Wallet Console.
    # service_account_json: the service-account key, either as raw JSON (what
    #   you paste into a Render env var) or as a path to the .json file.
    # origins: sites allowed to present the save link.
    # Leave issuer_id/service_account_json empty and the enrol endpoint returns
    # a 503 explaining what is missing, rather than a save URL that 404s.
    google_wallet_issuer_id: str = ""
    google_wallet_service_account_json: str = ""
    google_wallet_origins: str = "https://neophukubye.github.io"
    google_wallet_class_suffix: str = "smartmoney_momo_class"

    # Google OAuth (sign-in)
    # Comma-separated list of allowed Web Client IDs. The backend checks the
    # `aud` claim of incoming Google ID tokens against this list.
    google_client_ids: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
