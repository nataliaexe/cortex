"""Carregamento de configuracao do Cortex."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH, override=False)


def _expand(path: str | Path) -> Path:
    return Path(os.path.expanduser(str(path))).resolve()


class AppConfig(BaseModel):
    name: str = "cortex"
    version: str = "0.1.0"
    log_level: str = "info"
    log_file: str = "logs/cortex.log"


class DatabaseConfig(BaseModel):
    path: str = "data/cortex.db"
    vectors_path: str = "data/vectors"


class LocalModelConfig(BaseModel):
    provider: str = "ollama"
    host: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5-coder:7b"
    embed_model: str = "nomic-embed-text"
    timeout_seconds: int = 60


class ModelsConfig(BaseModel):
    local: LocalModelConfig


class ProviderConfig(BaseModel):
    enabled: bool = True
    kind: str = "openai_compatible"
    base_url: str
    api_key_env: str
    default_model: str
    models: list[str] = Field(default_factory=list)
    timeout_seconds: int = 90
    free: bool = False
    rate_limit_rpm: int | None = None
    cost_input_per_mtok: float | None = None
    cost_output_per_mtok: float | None = None
    extra_headers: dict[str, str] = Field(default_factory=dict)


class MemoryConfig(BaseModel):
    working_window_messages: int = 20
    episodic_retention_days: int = 365
    semantic_min_score: float = 0.35


class GovernanceConfig(BaseModel):
    default_action: str = "deny"
    dry_run_required: list[str] = Field(default_factory=list)


class FilesToolConfig(BaseModel):
    allowed_roots: list[str] = Field(default_factory=list)
    max_read_bytes: int = 2_000_000


class ShellToolConfig(BaseModel):
    allowlist_argv0: list[str] = Field(default_factory=list)
    forbid_shell_meta: bool = True
    timeout_seconds: int = 60


class ToolsConfig(BaseModel):
    files: FilesToolConfig = Field(default_factory=FilesToolConfig)
    shell: ShellToolConfig = Field(default_factory=ShellToolConfig)


class CortexConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    models: ModelsConfig
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)


# ---------- router ----------

class RouterConfig(BaseModel):
    tasks: dict[str, list[str]] = Field(default_factory=dict)
    model_overrides: dict[str, dict[str, str]] = Field(default_factory=dict)
    never_send_patterns: list[str] = Field(default_factory=list)
    never_send_regex: list[str] = Field(default_factory=list)


# ---------- carregamento ----------

def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


@lru_cache(maxsize=1)
def load_config(config_path: str | Path | None = None) -> CortexConfig:
    """Carrega config/cortex.yaml. Cacheado por processo."""
    if config_path is None:
        config_path = Path(os.environ.get("CORTEX_CONFIG", "config/cortex.yaml"))

    resolved_config = _expand(config_path)
    raw = _load_yaml(resolved_config)
    cfg = CortexConfig(**raw)

    root = resolved_config.parent.parent
    cfg.database.path = str((root / cfg.database.path).resolve())
    cfg.database.vectors_path = str((root / cfg.database.vectors_path).resolve())
    cfg.app.log_file = str((root / cfg.app.log_file).resolve())
    cfg.tools.files.allowed_roots = [str(_expand(r)) for r in cfg.tools.files.allowed_roots]

    return cfg


def load_policy(policy_path: str | Path | None = None) -> dict[str, Any]:
    """Carrega config/policy.yaml como dict cru (validado pelo authorizer)."""
    if policy_path is None:
        policy_path = Path(os.environ.get("CORTEX_POLICY", "config/policy.yaml"))
    return _load_yaml(_expand(policy_path))


@lru_cache(maxsize=1)
def load_router_config(router_path: str | Path | None = None) -> RouterConfig:
    """Carrega config/router.yaml. Cacheado por processo."""
    if router_path is None:
        router_path = Path(os.environ.get("CORTEX_ROUTER", "config/router.yaml"))

    raw = _load_yaml(_expand(router_path))
    return RouterConfig(
        tasks=raw.get("tasks", {}) or {},
        model_overrides=raw.get("model_overrides", {}) or {},
        never_send_patterns=(raw.get("privacy", {}) or {}).get("never_send_patterns", []) or [],
        never_send_regex=(raw.get("privacy", {}) or {}).get("never_send_regex", []) or [],
    )
