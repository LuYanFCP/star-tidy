import os
import json
import yaml
from typing import Dict, Any, Optional

class Config:
    """Configuration manager supporting environment variables, JSON and YAML files"""
    
    def __init__(self, config_file: str = None):
        self.config = {}
        self.load_config(config_file)
    
    def load_config(self, config_file: str = None):
        """Load configuration"""
        # Default configuration
        exclude_repos_str = os.environ.get("EXCLUDE_REPOS", "")
        exclude_repos = [repo.strip() for repo in exclude_repos_str.split(",") if repo.strip()]
        
        self.config = {
            "github_token": os.environ.get("GITHUB_TOKEN"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY"),
            "openai_api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
            "mode": os.environ.get("STAR_TIDY_MODE", "auto"),
            "exclude_repos": exclude_repos,
            "custom_categories": {},
            "max_repos_per_request": int(os.environ.get("MAX_REPOS_PER_REQUEST", "100")),
            "ai_model": os.environ.get("AI_MODEL", "gpt-4o-mini"),
            "max_tokens": int(os.environ.get("MAX_TOKENS", "0")) or None,
            "temperature": float(os.environ.get("TEMPERATURE", "0")) or None,
            "dry_run": os.environ.get("DRY_RUN", "false").lower() == "true",
            "summary_options": {
                "auto_complete": os.environ.get("AUTO_COMPLETE_SUMMARIES", "true").lower() == "true",
                "enhance_existing": os.environ.get("ENHANCE_EXISTING_SUMMARIES", "true").lower() == "true",
                "use_ai_summary": os.environ.get("USE_AI_SUMMARY", "true").lower() == "true",
                "include_stats": os.environ.get("INCLUDE_STATS", "true").lower() == "true",
            }
        }
        
        # Load from configuration file
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                
                # Merge configuration, file config has higher priority than environment variables
                self.config.update(file_config)
            except Exception as e:
                print(f"Warning: Failed to load config file {config_file}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def validate(self) -> bool:
        """Validate required configuration items"""
        required_keys = ["github_token", "openai_api_key"]
        missing_keys = []
        
        for key in required_keys:
            if not self.config.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration dictionary"""
        return self.config.copy()


def load_config(config_file: str = None) -> Config:
    """Convenience function to load configuration"""
    # Check for CONFIG_FILE environment variable first
    if not config_file:
        config_file = os.environ.get("CONFIG_FILE")
    
    # Try to load configuration file from common locations
    if not config_file:
        possible_files = [
            "config.yaml",
            "config.yml", 
            "config.json",
            ".star-tidy.yaml",
            ".star-tidy.yml",
            ".star-tidy.json"
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                config_file = file_path
                break
    
    return Config(config_file)


if __name__ == "__main__":
    # 测试配置加载
    try:
        config = load_config()
        config.validate()
        print("Configuration loaded successfully:")
        
        # 打印配置（隐藏敏感信息）
        config_dict = config.to_dict()
        for key, value in config_dict.items():
            if 'token' in key.lower() or 'key' in key.lower():
                display_value = f"{value[:8]}..." if value else "Not set"
            else:
                display_value = value
            print(f"  {key}: {display_value}")
            
    except Exception as e:
        print(f"Configuration error: {e}")