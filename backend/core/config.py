"""
File: backend/core/config.py
Advanced Configuration Management for Juggler
Supports YAML-based configuration with environment overrides
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import secrets

class DatabaseConfig(BaseModel):
    type: str = "sqlite"
    path: str = "data/juggler.db"
    echo: bool = False
    pool_size: int = 5

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    timeout: int = 300
    keepalive: int = 2
    reload: bool = False
    debug: bool = False

class ProviderConfig(BaseModel):
    enabled: bool = True
    base_url: Optional[str] = None
    timeout: int = 30
    default_model: Optional[str] = None

class SecurityConfig(BaseModel):
    secret_key: Optional[str] = None
    session_lifetime: int = 86400
    rate_limiting_enabled: bool = True
    requests_per_minute: int = 60
    burst_size: int = 10
    
    @field_validator('secret_key', mode='before')
    @classmethod
    def generate_secret_key(cls, v: Optional[str]) -> str:
        return v if v is not None else secrets.token_urlsafe(32)

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "structured"
    file: str = "logs/juggler.log"
    console: bool = True
    max_size: str = "10MB"
    backup_count: int = 5

class FeaturesConfig(BaseModel):
    conversation_export: bool = True
    parallel_queries: bool = True
    context_transfer: bool = True
    health_monitoring: bool = True
    admin_dashboard: bool = False

class SSLConfig(BaseModel):
    enabled: bool = False
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    redirect_http: bool = False

class JugglerConfig(BaseSettings):
    """Main configuration class for Juggler application"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: str = Field(default="development")
    
    # Application info
    app_name: str = "Juggler"
    app_version: str = "1.0.0"
    
    # Server settings
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Provider configurations
    ollama: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        base_url="http://localhost:11434",
        default_model="llama3:8b"
    ))
    groq: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        base_url="https://api.groq.com/openai/v1", 
        default_model="llama3-8b-8192"
    ))
    gemini: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        default_model="gemini-pro"
    ))
    openai: ProviderConfig = Field(default_factory=lambda: ProviderConfig(
        base_url="https://api.openai.com/v1",
        default_model="gpt-4"
    ))
    
    # API Keys (from environment only)
    groq_api_key: Optional[str] = Field(default=None)
    gemini_api_key: Optional[str] = Field(default=None) 
    openai_api_key: Optional[str] = Field(default=None)
    
    # Security
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Logging
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Features
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    
    # SSL/TLS
    ssl: SSLConfig = Field(default_factory=SSLConfig)
    
    # CORS settings
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    
    # Legacy properties for backward compatibility
    @property
    def GROQ_API_KEY(self) -> Optional[str]:
        return self.groq_api_key
    
    @property
    def GEMINI_API_KEY(self) -> Optional[str]:
        return self.gemini_api_key
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self.openai_api_key
    
    @property
    def OLLAMA_BASE_URL(self) -> str:
        return self.ollama.base_url or "http://localhost:11434"
    
    @property
    def DEBUG(self) -> bool:
        return self.server.debug
    
    @property
    def HOST(self) -> str:
        return self.server.host
    
    @property
    def PORT(self) -> int:
        return self.server.port
    
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API key is configured"""
        return self.gemini_api_key is not None and len(self.gemini_api_key.strip()) > 0
    
    def is_groq_configured(self) -> bool:
        """Check if Groq API key is configured"""
        return self.groq_api_key is not None and len(self.groq_api_key.strip()) > 0
    
    def is_openai_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return self.openai_api_key is not None and len(self.openai_api_key.strip()) > 0
    
    def get_configured_providers(self) -> List[str]:
        """Get list of configured providers"""
        providers: List[str] = []
        
        if self.ollama.enabled:
            providers.append("ollama")
        
        if self.groq.enabled and self.is_groq_configured():
            providers.append("groq")
        
        if self.gemini.enabled and self.is_gemini_configured():
            providers.append("gemini")
        
        if self.openai.enabled and self.is_openai_configured():
            providers.append("openai")
        
        return providers
    
    def print_config_summary(self) -> None:
        """Print configuration summary (without sensitive data)"""
        print(f"\n🔧 {self.app_name} Configuration Summary")
        print("=" * 40)
        print(f"Environment: {self.environment}")
        print(f"Debug Mode: {self.server.debug}")
        print(f"Host: {self.server.host}:{self.server.port}")
        print(f"Ollama URL: {self.OLLAMA_BASE_URL}")
        
        providers = self.get_configured_providers()
        print(f"Configured Providers: {', '.join(providers)}")
        
        print(f"Groq: {'✅ Configured' if self.is_groq_configured() else '❌ Not configured'}")
        print(f"Gemini: {'✅ Configured' if self.is_gemini_configured() else '❌ Not configured'}")
        print(f"OpenAI: {'✅ Configured' if self.is_openai_configured() else '❌ Not configured'}")
        print("=" * 40 + "\n")

class ConfigLoader:
    """Configuration loader with YAML support and environment overrides"""
    
    def __init__(self, config_dir: str = "config") -> None:
        self.config_dir = Path(config_dir)
        self.base_config: Dict[str, Any] = {}
        self.env_config: Dict[str, Any] = {}
        
    def load_config(self, environment: Optional[str] = None) -> JugglerConfig:
        """Load configuration from YAML files and environment"""
        
        # Determine environment
        if environment is None:
            environment = os.getenv("JUGGLER_ENV", "development")
        
        print(f"Loading configuration for environment: {environment}")
        
        # Load base configuration
        base_file = self.config_dir / "base.yaml"
        if base_file.exists():
            self.base_config = self._load_yaml_file(base_file)
            print(f"Loaded base config from {base_file}")
        
        # Load environment-specific configuration
        env_file = self.config_dir / "environments" / f"{environment}.yaml"
        if env_file.exists():
            self.env_config = self._load_yaml_file(env_file)
            print(f"Loaded environment config from {env_file}")
        
        # Merge configurations
        merged_config = self._merge_configs(self.base_config, self.env_config)
        
        # Load environment variables
        load_dotenv()
        
        # Create Pydantic config with merged YAML + env vars
        config = JugglerConfig(**merged_config)
        
        # Validate configuration
        validation_result = self._validate_config(config)
        if validation_result["errors"]:
            print("Configuration validation errors:")
            for error in validation_result["errors"]:
                print(f"  • {error}")
        
        if validation_result["warnings"]:
            print("Configuration warnings:")
            for warning in validation_result["warnings"]:
                print(f"  • {warning}")
        
        return config
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file safely"""
        try:
            with open(str(file_path), 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if content is not None else {}
        except FileNotFoundError:
            print(f"Configuration file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in env.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self, config: JugglerConfig) -> Dict[str, List[str]]:
        """Validate configuration and return errors/warnings"""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Check provider API keys
        if config.groq.enabled and not config.groq_api_key:
            warnings.append("Groq enabled but no API key provided")
        
        if config.gemini.enabled and not config.gemini_api_key:
            warnings.append("Gemini enabled but no API key provided")
        
        if config.openai.enabled and not config.openai_api_key:
            warnings.append("OpenAI enabled but no API key provided")
        
        # Check database path
        db_path = Path(config.database.path)
        db_dir = db_path.parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory {db_dir}: {e}")
        
        # Check log directory
        log_path = Path(config.logging.file)
        log_dir = log_path.parent
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                warnings.append(f"Cannot create log directory {log_dir}: {e}")
        
        # Check SSL configuration
        if config.ssl.enabled:
            if not config.ssl.cert_file or not config.ssl.key_file:
                errors.append("SSL enabled but cert_file or key_file not specified")
            else:
                cert_path = Path(config.ssl.cert_file)
                key_path = Path(config.ssl.key_file)
                if not cert_path.exists() or not key_path.exists():
                    errors.append("SSL certificate files do not exist")
        
        return {
            "errors": errors,
            "warnings": warnings
        }

def create_example_config() -> None:
    """Create example configuration files"""
    config_dir = Path("config")
    
    # Create directories
    config_dir.mkdir(exist_ok=True)
    (config_dir / "environments").mkdir(exist_ok=True)
    (config_dir / "secrets").mkdir(exist_ok=True)
    
    # Create example .env
    env_example = """# Juggler Configuration - Environment Variables
# Copy this to .env and fill in your API keys

# AI Provider API Keys
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Environment
JUGGLER_ENV=development

# Security
SECRET_KEY=your_secret_key_here

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Optional overrides
# SERVER__PORT=8001
# LOGGING__LEVEL=DEBUG
"""
    
    env_file_path = config_dir / "secrets" / ".env.example"
    with open(env_file_path, "w", encoding="utf-8") as f:
        f.write(env_example)
    
    print(f"Created example configuration in {config_dir}/")
    print("Copy config/secrets/.env.example to .env and configure your API keys")

# Global configuration instance
_config_loader: Optional[ConfigLoader] = None
_config_instance: Optional[JugglerConfig] = None

def get_config_loader() -> ConfigLoader:
    """Get or create the config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def get_config(environment: Optional[str] = None) -> JugglerConfig:
    """Get the global configuration instance"""
    global _config_instance
    
    if _config_instance is None:
        loader = get_config_loader()
        _config_instance = loader.load_config(environment)
    
    return _config_instance

def reload_config(environment: Optional[str] = None) -> JugglerConfig:
    """Force reload configuration"""
    global _config_instance
    _config_instance = None
    return get_config(environment)

# Backward compatibility with old Config class
class LegacyConfig:
    """Legacy configuration interface for backward compatibility"""
    
    def __init__(self, modern_config: JugglerConfig) -> None:
        self._config = modern_config
    
    @property
    def GROQ_API_KEY(self) -> Optional[str]:
        return self._config.groq_api_key
    
    @property
    def GEMINI_API_KEY(self) -> Optional[str]:
        return self._config.gemini_api_key
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self._config.openai_api_key
    
    @property
    def OLLAMA_BASE_URL(self) -> str:
        return self._config.ollama.base_url or "http://localhost:11434"
    
    @property
    def DEBUG(self) -> bool:
        return self._config.server.debug
    
    @property
    def HOST(self) -> str:
        return self._config.server.host
    
    @property
    def PORT(self) -> int:
        return self._config.server.port
    
    def is_gemini_configured(self) -> bool:
        return self._config.is_gemini_configured()
    
    def is_groq_configured(self) -> bool:
        return self._config.is_groq_configured()
    
    def is_openai_configured(self) -> bool:
        return self._config.is_openai_configured()
    
    def get_configured_providers(self) -> List[str]:
        return self._config.get_configured_providers()
    
    def print_config_summary(self) -> None:
        return self._config.print_config_summary()

def get_legacy_config() -> LegacyConfig:
    """Get legacy-compatible config instance"""
    return LegacyConfig(get_config())

if __name__ == "__main__":
    # Create example configuration
    create_example_config()
    
    # Load and display configuration
    config = get_config()
    config.print_config_summary()
    print(f"Configuration loaded successfully for {config.environment} environment")
    print(f"Available providers: {config.get_configured_providers()}")