import os
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Config:
    api_key: str
    model: str
    base_url: str
    temperature: float = 0.2
    max_retries: int = 3
    timeout: int = 60


def load_config() -> Config:
    config_path = Path.cwd() / "config.yaml"
    if not config_path.exists():
        print("Error: 未找到 config.yaml，请在当前目录创建配置文件。", file=sys.stderr)
        print("参考模板：config.yaml.example", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    env_api_key = os.environ.get("TESTGEN_API_KEY")
    if env_api_key:
        data["api_key"] = env_api_key

    missing = [k for k in ("api_key", "model", "base_url") if not data.get(k)]
    if missing:
        print(f"Error: config.yaml 缺少必填字段: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return Config(
        api_key=data["api_key"],
        model=data["model"],
        base_url=data["base_url"],
        temperature=float(data.get("temperature", 0.2)),
        max_retries=int(data.get("max_retries", 3)),
        timeout=int(data.get("timeout", 60)),
    )
