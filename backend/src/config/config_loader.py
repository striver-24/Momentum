import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Centralized configuration loader for the Momentum agent.
    Loads and validates configuration from YAML file.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            self._validate_config()
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _validate_config(self):
        """Validate required configuration sections exist."""
        required_sections = [
            'models', 'vector_db', 'file_system', 'git', 
            'agent', 'languages', 'prompts', 'status_messages'
        ]
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration value (e.g., 'models.embedding.name')
            default: Default value to return if key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                value = value[key]
            
            return value
        
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise KeyError(f"Configuration key not found: {key_path}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()

# Global configuration instance
_config_instance = None

def get_config() -> ConfigLoader:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance

def reload_config():
    """Reload the global configuration."""
    global _config_instance
    if _config_instance:
        _config_instance.reload()
    else:
        _config_instance = ConfigLoader()

# Convenience functions for common configuration access patterns
def get_model_config(model_type: str) -> Dict[str, Any]:
    """Get model configuration for embedding or llm."""
    return get_config().get_section(f'models.{model_type}')

def get_language_config(language: str) -> Dict[str, Any]:
    """Get language-specific configuration."""
    return get_config().get_section(f'languages.{language}')

def get_prompt_template(prompt_type: str) -> str:
    """Get prompt template."""
    return get_config().get(f'prompts.{prompt_type}.template')

def get_status_message(category: str, message_type: str) -> str:
    """Get status message template."""
    return get_config().get(f'status_messages.{category}.{message_type}')

def get_file_paths() -> Dict[str, str]:
    """Get default file paths."""
    return get_config().get_section('file_system')

def get_agent_config() -> Dict[str, Any]:
    """Get agent behavior configuration."""
    return get_config().get_section('agent')

def get_git_config() -> Dict[str, Any]:
    """Get git configuration."""
    return get_config().get_section('git')

def get_vector_db_config() -> Dict[str, Any]:
    """Get vector database configuration."""
    return get_config().get_section('vector_db')