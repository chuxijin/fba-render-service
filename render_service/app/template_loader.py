#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tomllib
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from render_service.app.config import settings
from render_service.app.schemas import (
    RenderAnswerLayout,
    RenderDeliveryMode,
    RenderVariant,
    TemplateSummary,
)

_MATH_PATTERN = re.compile(
    r'(\$\$.*?\$\$|\$[^$\n]+\$|\\\(.+?\\\)|\\\[.+?\\\])',
    re.DOTALL,
)

_CIRCLED_NUMBER_REPLACEMENTS: dict[str, str] = {}


def _escape_text_preserving_math(value: str) -> str:
    parts: list[str] = []
    last_end = 0
    for match in _MATH_PATTERN.finditer(value):
        if match.start() > last_end:
            parts.append(tex_escape(value[last_end:match.start()]))
        parts.append(match.group(0))
        last_end = match.end()
    if last_end < len(value):
        parts.append(tex_escape(value[last_end:]))
    return ''.join(parts)


def _compact_whitespace(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip()


def tex_escape(value: object) -> str:
    text = '' if value is None else str(value)
    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    replacements.update(_CIRCLED_NUMBER_REPLACEMENTS)
    return ''.join(replacements.get(char, char) for char in text)


def _plain_text_to_tex(text: str) -> str:
    escaped = tex_escape(text)
    normalized = escaped.replace('\r\n', '\n').replace('\r', '\n')
    normalized = normalized.replace('\n\n', '\n\\par\n')
    return normalized.replace('\n', '\\\\\n')


def _node_to_tex(node: NavigableString | Tag, *, in_list: bool = False) -> str:
    if isinstance(node, NavigableString):
        return _escape_text_preserving_math(str(node))

    name = node.name.lower() if node.name else ''
    children = ''.join(_node_to_tex(child, in_list=in_list) for child in node.children)

    if name in {'strong', 'b'}:
        return f'\\textbf{{{children}}}'
    if name in {'em', 'i'}:
        return f'\\textit{{{children}}}'
    if name == 'u':
        return f'\\underline{{{children}}}'
    if name in {'sub', 'sup'}:
        marker = '_' if name == 'sub' else '^'
        return f'${marker}{{{children}}}$'
    if name in {'math'}:
        compact = _compact_whitespace(children)
        return f'${compact}$'
    if name == 'code':
        compact = _compact_whitespace(children)
        return f'\\texttt{{{compact}}}'
    if name == 'pre':
        compact = _compact_whitespace(children)
        return f'\\par\\texttt{{{compact}}}\\par\n'
    if name in {'blockquote'}:
        return f'\\begin{{quote}}{children}\\end{{quote}}\n'
    if name in {'hr'}:
        return '\\par\\noindent\\rule{\\linewidth}{0.4pt}\\par\n'
    if name == 'br':
        return '\\par\n'
    if name in {'h1', 'h2', 'h3', 'h4'}:
        return f'\\par\\textbf{{{children}}}\\par\n'
    if name in {'p', 'div', 'section', 'article'}:
        return f'{children}\\par\n'
    if name in {'table'}:
        rows = [row for row in node.find_all('tr')]
        if not rows:
            return ''
        max_cols = 0
        rendered_rows: list[list[str]] = []
        for row in rows:
            cells = row.find_all(['th', 'td'])
            rendered_cells: list[str] = []
            for cell in cells:
                cell_tex = ''.join(_node_to_tex(child, in_list=False) for child in cell.children)
                cell_tex = _compact_whitespace(cell_tex.replace('\\par', ' ').replace('\n', ' '))
                if cell.name and cell.name.lower() == 'th':
                    cell_tex = f'\\textbf{{{cell_tex}}}'
                rendered_cells.append(cell_tex or ' ')
            rendered_rows.append(rendered_cells)
            max_cols = max(max_cols, len(rendered_cells))

        if max_cols <= 0:
            return ''

        col_spec = '|'.join(['X'] * max_cols)
        lines = [
            '\\par',
            '\\noindent',
            f'\\begin{{tabularx}}{{\\linewidth}}{{|{col_spec}|}}',
            '\\hline',
        ]
        for row in rendered_rows:
            padded = row + ([' '] * (max_cols - len(row)))
            lines.append(' & '.join(padded) + r' \\')
            lines.append('\\hline')
        lines.append('\\end{tabularx}')
        lines.append('\\par')
        return '\n'.join(lines) + '\n'
    if name == 'a':
        href = tex_escape((node.get('href') or '').strip())
        if href:
            text_value = children or href
            return f'\\href{{{href}}}{{{text_value}}}'
        return children
    if name == 'img':
        src = tex_escape((node.get('src') or node.get('_src') or '').strip())
        alt = tex_escape((node.get('alt') or '').strip())
        if src.startswith('assets/'):
            return f'\\par\\noindent\\includegraphics[width=0.92\\linewidth]{{{src}}}\\par\n'
        if src:
            return f'\\par{{\\small\\textcolor{{inkmuted}}{{[图片] {alt or "见链接"}：\\url{{{src}}}}}}}\\par\n'
        return f'\\par{{\\small\\textcolor{{inkmuted}}{{[图片] {alt or "无链接"}}}}}\\par\n'
    if name == 'ul':
        items = [
            _node_to_tex(child, in_list=True).strip()
            for child in node.children
            if isinstance(child, Tag) and child.name and child.name.lower() == 'li'
        ]
        if not items:
            return ''
        body = '\n'.join(f'\\item {item}' for item in items)
        return f'\\begin{{itemize}}\n{body}\n\\end{{itemize}}\n'
    if name == 'ol':
        items = [
            _node_to_tex(child, in_list=True).strip()
            for child in node.children
            if isinstance(child, Tag) and child.name and child.name.lower() == 'li'
        ]
        if not items:
            return ''
        body = '\n'.join(f'\\item {item}' for item in items)
        return f'\\begin{{enumerate}}\n{body}\n\\end{{enumerate}}\n'
    if name == 'li':
        if in_list:
            return children
        return f'\\item {children}\n'

    return children


def html_to_tex(value: object) -> str:
    text = '' if value is None else str(value)
    if not text.strip():
        return ''
    if not re.search(r'<[a-zA-Z][^>]*>', text):
        return _plain_text_to_tex(text)

    soup = BeautifulSoup(text, 'html.parser')
    converted = ''.join(_node_to_tex(node) for node in soup.contents)
    converted = converted.replace('\n\n', '\n').strip()
    return converted or _plain_text_to_tex(text)


def html_plain_text(value: object) -> str:
    text = '' if value is None else str(value)
    if not text.strip():
        return ''
    if not re.search(r'<[a-zA-Z][^>]*>', text):
        return _compact_whitespace(text)

    soup = BeautifulSoup(text, 'html.parser')
    return _compact_whitespace(soup.get_text(' ', strip=True))


def option_layout_columns(value: object) -> int:
    if not isinstance(value, list) or not value:
        return 1

    estimated_lengths: list[int] = []
    for item in value:
        if not isinstance(item, dict):
            return 1
        raw = str(item.get('content_tex') or item.get('content_text') or '')
        lowered = raw.lower()
        if (
            '\\includegraphics' in raw
            or '\\begin{' in raw
            or '<img' in lowered
            or '<table' in lowered
            or '<svg' in lowered
            or '$$' in raw
            or '\\[' in raw
        ):
            return 1

        plain = html_plain_text(raw)
        estimated_lengths.append(len(plain))

    if not estimated_lengths:
        return 1

    max_len = max(estimated_lengths)
    avg_len = sum(estimated_lengths) / len(estimated_lengths)

    if len(value) >= 4 and max_len <= 12 and avg_len <= 8:
        return 4
    if max_len <= 26 and avg_len <= 18:
        return 2
    return 1


def build_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(settings.templates_root)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    env.filters['tex_escape'] = tex_escape
    env.filters['html_to_tex'] = html_to_tex
    env.filters['html_plain_text'] = html_plain_text
    env.filters['option_layout_columns'] = option_layout_columns
    return env


def load_manifest(template_key: str) -> TemplateSummary:
    manifest_path = settings.templates_root / template_key / 'manifest.toml'
    if not manifest_path.exists():
        return TemplateSummary(key=template_key, name=template_key, template_source=template_key)

    payload = tomllib.loads(manifest_path.read_text(encoding='utf-8'))
    variant_entrypoints = payload.get('variant_entrypoints', {}) or {}
    default_variant = payload.get('default_variant', 'questions_only')
    if default_variant not in variant_entrypoints and payload.get('entrypoint'):
        variant_entrypoints[default_variant] = payload.get('entrypoint', 'main.tex.j2')
    if 'questions_only' not in variant_entrypoints:
        variant_entrypoints['questions_only'] = payload.get('entrypoint', 'main.tex.j2')

    return TemplateSummary(
        key=payload.get('key', template_key),
        name=payload.get('name', template_key),
        description=payload.get('description', ''),
        entrypoint=payload.get('entrypoint', 'main.tex.j2'),
        template_source=payload.get('template_source', template_key),
        default_variant=default_variant,
        supported_variants=list(variant_entrypoints.keys()),
        variant_entrypoints=variant_entrypoints,
    )


def list_templates() -> list[TemplateSummary]:
    if not settings.templates_root.exists():
        return []
    templates: list[TemplateSummary] = []
    for template_dir in sorted(path for path in settings.templates_root.iterdir() if path.is_dir()):
        templates.append(load_manifest(template_dir.name))
    return templates


def _resolve_render_variant_from_context(context: dict) -> RenderVariant | None:
    explicit_variant = context.get('render_variant')
    if explicit_variant:
        return explicit_variant

    render_plan = context.get('render_plan')
    if not isinstance(render_plan, dict):
        return None

    selected_variant = render_plan.get('selected_variant')
    if selected_variant:
        return selected_variant

    candidates = render_plan.get('render_variants')
    if isinstance(candidates, list):
        for item in candidates:
            if isinstance(item, str) and item:
                return item

    content_mode = render_plan.get('content_mode')
    answer_layout = render_plan.get('answer_layout')
    delivery_mode = render_plan.get('delivery_mode')
    inferred = _resolve_render_variant_from_export_config(
        content_mode=content_mode,
        answer_layout=answer_layout,
        delivery_mode=delivery_mode,
    )
    if inferred:
        return inferred
    return None


def _resolve_render_variant_from_export_config(
    *,
    content_mode: str | None,
    answer_layout: str | None,
    delivery_mode: str | None,
) -> RenderVariant | None:
    if content_mode == 'questions_only':
        return 'questions_only'

    if content_mode != 'questions_with_answers':
        return None

    resolved_answer_layout: RenderAnswerLayout = 'inline' if answer_layout == 'inline' else 'appendix'
    resolved_delivery_mode: RenderDeliveryMode = 'split_pdf' if delivery_mode == 'split_pdf' else 'single_pdf'

    if resolved_answer_layout == 'inline':
        return 'combined_inline'
    if resolved_delivery_mode == 'split_pdf':
        return 'questions_only'
    return 'combined_appendix'


def resolve_entrypoint(
    manifest: TemplateSummary,
    context: dict,
    render_variant: RenderVariant | None,
) -> tuple[RenderVariant, str]:
    resolved_variant = render_variant or _resolve_render_variant_from_context(context) or manifest.default_variant
    entrypoint = manifest.variant_entrypoints.get(resolved_variant)
    if entrypoint is None:
        raise ValueError(f'模板 {manifest.key} 不支持渲染变体 {resolved_variant}')
    return resolved_variant, entrypoint


def render_template(template_key: str, context: dict, render_variant: RenderVariant | None = None) -> tuple[TemplateSummary, RenderVariant, str, str]:
    manifest = load_manifest(template_key)
    env = build_environment()
    resolved_variant, entrypoint = resolve_entrypoint(manifest, context, render_variant)
    template_root = manifest.template_source or manifest.key
    template = env.get_template(f'{template_root}/{entrypoint}')
    render_context = dict(context)
    render_context['render_variant'] = resolved_variant
    render_context['template_manifest'] = manifest.model_dump(mode='json')
    rendered = template.render(**render_context)
    return manifest, resolved_variant, entrypoint, rendered
