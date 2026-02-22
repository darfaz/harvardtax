from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # QBO
    qbo_client_id: str = ""
    qbo_client_secret: str = ""
    qbo_redirect_uri: str = "http://localhost:8000/auth/qbo/callback"
    qbo_environment: str = "sandbox"  # sandbox or production
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    
    # Claude
    anthropic_api_key: str = ""
    
    # App
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"

settings = Settings()
