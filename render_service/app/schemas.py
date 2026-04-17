#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

RenderVariant = Literal['questions_only', 'solutions_only', 'combined_inline', 'combined_appendix']
RenderContentMode = Literal['questions_only', 'questions_with_answers']
RenderAnswerLayout = Literal['inline', 'appendix']
RenderDeliveryMode = Literal['single_pdf', 'split_pdf']


class TemplateSummary(BaseModel):
    key: str
    name: str
    description: str = ''
    entrypoint: str = 'main.tex.j2'
    template_source: str | None = None
    default_variant: RenderVariant = 'questions_only'
    supported_variants: list[RenderVariant] = Field(default_factory=lambda: ['questions_only'])
    variant_entrypoints: dict[str, str] = Field(default_factory=dict)


class RenderRequest(BaseModel):
    template_key: str = Field(..., min_length=1, max_length=100)
    job_id: str | None = Field(default=None, max_length=64)
    render_variant: RenderVariant | None = None
    compile_pdf: bool = True
    keep_workdir: bool = True
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator('template_key')
    @classmethod
    def validate_template_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError('template_key 不能为空。')
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        if any(char not in allowed for char in normalized):
            raise ValueError('template_key 仅支持字母、数字、下划线和短横线。')
        return normalized


class RenderResponse(BaseModel):
    job_id: str
    template_key: str
    render_variant: RenderVariant
    entrypoint: str
    status: str
    compile_pdf: bool
    workdir: str
    tex_path: str
    pdf_path: str | None = None
    log_path: str | None = None
    pdf_download_path: str | None = None
    log_download_path: str | None = None
    preview_download_paths: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def new_job_id() -> str:
    return uuid4().hex
