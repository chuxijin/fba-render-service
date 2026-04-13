#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import shutil
import subprocess
from pathlib import Path

from render_service.app.config import settings


def ensure_directories() -> None:
    settings.data_root.mkdir(parents=True, exist_ok=True)
    settings.output_root.mkdir(parents=True, exist_ok=True)
    settings.work_root.mkdir(parents=True, exist_ok=True)


def create_job_workspace(job_id: str, render_variant: str | None = None) -> Path:
    ensure_directories()
    workspace = settings.work_root / job_id
    if render_variant:
        workspace = workspace / render_variant
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def write_request_snapshot(workspace: Path, payload: dict) -> Path:
    request_path = workspace / 'request.json'
    request_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return request_path


def _variant_stem(render_variant: str) -> str:
    return f'main_{render_variant}'


def write_tex_file(workspace: Path, tex_source: str, render_variant: str) -> Path:
    tex_path = workspace / f'{_variant_stem(render_variant)}.tex'
    tex_path.write_text(tex_source, encoding='utf-8')
    return tex_path


def compile_pdf(workspace: Path, render_variant: str) -> tuple[Path, Path]:
    stem = _variant_stem(render_variant)
    command = [
        settings.latex_command,
        '-xelatex',
        '-interaction=nonstopmode',
        '-halt-on-error',
        '-file-line-error',
        '-outdir=' + str(workspace),
        str(workspace / f'{stem}.tex'),
    ]
    result = subprocess.run(command, cwd=workspace, capture_output=True, text=True, check=False)
    log_path = workspace / f'{stem}.log'
    combined_output = result.stdout + '\n' + result.stderr
    log_path.write_text(combined_output, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f'LaTeX 编译失败，详情见日志：{log_path}')

    generated_pdf = workspace / f'{stem}.pdf'
    if not generated_pdf.exists():
        raise RuntimeError('LaTeX 编译完成，但未找到输出 PDF。')
    return generated_pdf, log_path


def publish_pdf(job_id: str, render_variant: str, generated_pdf: Path) -> Path:
    target_path = settings.output_root / f'{job_id}_{render_variant}.pdf'
    shutil.copy2(generated_pdf, target_path)
    return target_path


def cleanup_auxiliary_files(workspace: Path) -> None:
    if not settings.cleanup_aux_files:
        return
    keep_names = {'request.json'}
    for child in workspace.iterdir():
        if child.name in keep_names or child.suffix in {'.tex', '.pdf', '.log'}:
            continue
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)
