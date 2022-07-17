from pydantic import BaseSettings, FilePath
from typing import Any, Dict
import yaml
from pathlib import Path


def yaml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a JSON file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """
    with open("config.yml") as f:
        config_dict = yaml.safe_load(f)

    return config_dict


class Settings(BaseSettings):
    # ovmf_path: FilePath
    # default_image_path: FilePath

    vm_default_memory: int = 4096
    vm_default_number_of_cores: int = 1
    vm_max_memory: int = 16 * 1024
    vm_min_memory: int = 128
    vm_max_number_of_cores: int = 4

    ovmf_path: Path
    default_image_path: Path

    class Config:
        env_prefix = "aleph_scrn_"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yaml_config_settings_source,
                env_settings,
                file_secret_settings,
            )


settings = Settings()
