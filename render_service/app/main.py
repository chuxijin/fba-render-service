#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from jinja2 import TemplateNotFound

from render_service.app.asset_localizer import localize_context_images
from render_service.app.config import settings
from render_service.app.latex import (
    cleanup_auxiliary_files,
    compile_pdf,
    create_job_workspace,
    ensure_directories,
    publish_pdf,
    write_request_snapshot,
    write_tex_file,
)
from render_service.app.schemas import RenderRequest, RenderResponse, new_job_id
from render_service.app.template_loader import list_templates, render_template
from render_service.app.template_loader import load_manifest, resolve_entrypoint


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_directories()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


def build_artifact_route(job_id: str, render_variant: str, artifact_kind: str) -> str:
    return f'/api/v1/jobs/{job_id}/artifacts/{render_variant}/{artifact_kind}'


def resolve_artifact_path(job_id: str, render_variant: str, artifact_kind: str) -> Path:
    if artifact_kind == 'pdf':
        return settings.output_root / f'{job_id}_{render_variant}.pdf'
    if artifact_kind == 'log':
        return settings.work_root / job_id / render_variant / f'main_{render_variant}.log'
    raise HTTPException(status_code=404, detail=f'不支持的产物类型：{artifact_kind}')


@app.get('/healthz')
async def healthz() -> dict:
    return {
        'status': 'ok',
        'compile_enabled': settings.compile_enabled,
        'templates': [item.model_dump() for item in list_templates()],
        'templates_root': str(settings.templates_root),
        'output_root': str(settings.output_root),
    }


@app.get('/api/v1/templates')
async def get_templates() -> list[dict]:
    return [item.model_dump() for item in list_templates()]


@app.get('/api/v1/jobs/{job_id}/artifacts/{render_variant}/{artifact_kind}')
async def get_job_artifact(job_id: str, render_variant: str, artifact_kind: str):
    artifact_path = resolve_artifact_path(job_id, render_variant, artifact_kind)
    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=404, detail='产物不存在。')

    media_type = 'application/pdf' if artifact_kind == 'pdf' else 'text/plain; charset=utf-8'
    return FileResponse(
        path=artifact_path,
        media_type=media_type,
        filename=artifact_path.name,
    )


@app.post('/api/v1/render', response_model=RenderResponse)
async def render_book(payload: RenderRequest) -> RenderResponse:
    job_id = payload.job_id or new_job_id()
    manifest_for_variant = load_manifest(payload.template_key)
    resolved_variant, _ = resolve_entrypoint(manifest_for_variant, payload.context, payload.render_variant)
    workspace = create_job_workspace(job_id, resolved_variant)
    localized_context = await localize_context_images(context=payload.context, workspace=workspace)

    try:
        manifest, render_variant, entrypoint, tex_source = render_template(
            payload.template_key,
            localized_context,
            resolved_variant,
        )
    except TemplateNotFound as exc:
        raise HTTPException(status_code=404, detail=f'模板不存在：{payload.template_key}') from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f'模板渲染失败：{exc}') from exc

    workspace = create_job_workspace(job_id, render_variant)
    request_payload = payload.model_dump(mode='json')
    request_payload['context'] = localized_context
    request_payload['render_variant'] = render_variant
    request_payload['resolved_entrypoint'] = entrypoint
    write_request_snapshot(workspace, request_payload)

    tex_path = write_tex_file(workspace, tex_source, render_variant)
    pdf_path = None
    log_path = None
    status = 'rendered'

    if payload.compile_pdf:
        if not settings.compile_enabled:
            raise HTTPException(status_code=409, detail='当前服务未开启 PDF 编译能力。')
        try:
            generated_pdf, latex_log_path = compile_pdf(workspace, render_variant)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        pdf_path = publish_pdf(job_id, render_variant, generated_pdf)
        log_path = latex_log_path
        status = 'compiled'
        cleanup_auxiliary_files(workspace)

    return RenderResponse(
        job_id=job_id,
        template_key=manifest.key,
        render_variant=render_variant,
        entrypoint=entrypoint,
        status=status,
        compile_pdf=payload.compile_pdf,
        workdir=str(workspace),
        tex_path=str(tex_path),
        pdf_path=str(pdf_path) if pdf_path else None,
        log_path=str(log_path) if log_path else None,
        pdf_download_path=build_artifact_route(job_id, render_variant, 'pdf') if pdf_path else None,
        log_download_path=build_artifact_route(job_id, render_variant, 'log') if log_path else None,
    )
