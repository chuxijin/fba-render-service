#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).resolve().parents[1]


def _prefer_container_path(container_path: str, local_path: Path) -> Path:
    candidate = Path(container_path)
    return candidate if candidate.exists() else local_path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='RENDER_SERVICE_', extra='ignore')

    app_name: str = 'FBA Render Service'
    host: str = '0.0.0.0'
    port: int = 9000
    data_root: Path = _prefer_container_path('/data', APP_ROOT)
    templates_root: Path = _prefer_container_path('/app/render_service/templates', APP_ROOT / 'templates')
    fonts_root: Path = _prefer_container_path('/app/render_service/fonts', APP_ROOT / 'fonts')
    output_root: Path = _prefer_container_path('/data/output', APP_ROOT / 'output')
    work_root: Path = _prefer_container_path('/data/workdir', APP_ROOT / 'workdir')
    compile_enabled: bool = True
    cleanup_aux_files: bool = True
    latex_command: str = 'latexmk'


settings = Settings()
