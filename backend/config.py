from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='PS3_', env_file='.env', extra='ignore')
    data_dir: Path = Path('data/device-a')
    cloud_dir: Path = Path('data/cloud')
    cloud_url: str = ''
    sync_token: str = ''
    embedding_model: str = 'BAAI/bge-small-en-v1.5'
    model_cache: str = 'data/models'
    local_model_url: str = 'http://127.0.0.1:11434/v1'
    local_model: str = 'qwen2.5:3b'
    cloud_model_url: str = ''
    cloud_model: str = ''
    cloud_api_key: str = ''
    cloud_timeout_seconds: float = 20
    cloud_fallback_to_local: bool = True
    local_timeout_seconds: float = 90

