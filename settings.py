#!/usr/bin/env python3

"""
Configuration management for RLHF Data Quality System.

This module provides environment-aware configuration using Pydantic BaseSettings with runtime validation, type coercion, and .env file support.

"""

# ----------------- Futures  ---------------
from __future__ import annotations

# ----------------- Standard Library ------------
import logging
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

# ----------------- Third Party Library --------------

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ------------------- Constants -------------------
_ENV_PREFIX: Final[str] = "RLHF_"
_LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# -------------------- Configuration ---------------

class AppConfig(BaseSettings):
    """
    Application configuration with environment variable support.

    Environment variables are prefixed with RLHF_ (e.g., RLHF_ENV_NAME=prod).
    Configuration can be loaded from .env files in development.
    """

    model_config = SettingsConfigDict(
        env_prefix=_ENV_PREFIX,
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,
        extra="ignore",
    )
    
    # Environment
    env_name: Literal["dev", "test", "prod"] = Field(default="dev",description="Runtime environment")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO",description="Application log level")

    # Paths
    db_path: Path = Field(
        default=Path("data/rlhf.db"),
        description="SQLite database path"
    )

    cache_dir: Path = Field(
        default=Path(".cache"),
        description="Cache directory for embeddings and checkpoints"
    )

    # Model Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for semantic similarity"
    )

    embedding_batch_size: int = Field(
        default = 32,
        ge = 1,
        le = 256,
        description = "Batch size for embedding generation"
    )

    # Detection Thresholds
    similarity_threshold: float = Field(
        default = 0.95,
        ge = 0.0, 
        le = 1.0,
        description = "Cosine similarity threshold for semantic duplicate detection"
    )

    length_ratio_threshold: float = Field(
        default = 3.0,
        ge = 1.0,
        description= "Maximum length ratio between chosen and rejected responses"        
    )

    # Processing
    checkpoint_interval: int = Field(
        default = 1000,
        ge = 100,
        description = "Save checkpoint every N pairs processed"
    )

    @field_validator("db_path", "cache_dir")
    @classmethod
    def ensure_parent_exists(cls, v: Path) -> Path:
        """ Create parent directories if they don't exist."""
        v.parent.mkdir(parents = True, exist_ok = True)
        return v
    
    @field_validator("cache_dir")
    @classmethod
    def ensure_cache_exists(cls, v: Path) -> Path:
        """Create cache directory if it doesn't exist"""
        v.mkdir(parents = True, exist_ok = True)
        return v

@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Get singleton configuration instance.
        
    Cached to ensure single source of truth across application.
    """
    return AppConfig()
