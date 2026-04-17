import sys
from pathlib import Path
import asyncio

# 添加 render_pdf 的项目根目录
sys.path.insert(0, str(Path("D:/100_Work/101_Program/Proj/render_pdf")))

from render_service.app.template_loader import render_template
from render_service.app.latex import create_job_workspace, write_tex_file, compile_pdf
from render_service.app.asset_localizer import localize_context_images
from render_service.app.preview_generator import generate_pdf_previews

async def main():
    job_id = 'practice_render_demo_5'
    workspace = create_job_workspace(job_id, 'questions_only')
    context = {
        'render_plan': {},
        'metadata': {
            'practice_cover_username': 'Antigravity (AI)',
            'practice_cover_avatar': 'https://avatars.githubusercontent.com/u/10137?v=4',
            'practice_cover_img': 'https://s.cn.bing.net/th?id=OHR.BistiBadlands_ZH-CN8762514930_1920x1080.jpg',
            'practice_cover_motto': '少年何妨梦摘星，敢挽桑弓射玉衡。',
            'practice_cover_update_time': '2026-04-14 17:00:00',
            'practice_cover_badge': '错题回刷',
            'subject': '行政职业能力测验'
        },
        'options': {
            'layout_mode': 'standard',
            'theme': 'vintage',
            'double_sided': True,
        },
        'book': {
            'title': '2026年行测极限刷题计划',
            'subtitle': '第五模块 - 数量关系错题解析',
        },
        'paper': {
            'question_count': 15,
            'material_count': 2,
            'sections': [
                {
                    'title': '一、数字推理',
                    'questions': [
                        {
                            'number': 1,
                            'stem_text': '<p>求数列 1, 1, 2, 3, 5, 8, ... 的通项公式</p>',
                            'options': [
                                {'key': 'A', 'content_text': 'A'},
                                {'key': 'B', 'content_text': 'B'},
                                {'key': 'C', 'content_text': 'C'},
                                {'key': 'D', 'content_text': 'D'}
                            ]
                        }
                    ]
                }
            ]
        }
    }
    
    print("下载图片与重定位路径...")
    localized_context = await localize_context_images(context=context, workspace=workspace)

    print("应用 Jinja2 模板...")
    manifest, render_variant, entrypoint, tex_source = render_template(
        template_key='practice',
        context=localized_context,
        render_variant='questions_only'
    )

    tex_path = write_tex_file(workspace, tex_source, render_variant)
    print('写入 .tex 完成:', tex_path)
    
    print("开始编译 PDF...")
    pdf_path, log_path = compile_pdf(workspace, render_variant)
    print('PDF 生成完毕! ->', pdf_path)
    
    previews = generate_pdf_previews(pdf_path, output_dir=workspace/"previews", max_pages=5)
    print(f'已生成 {len(previews)} 张预览图：')
    for p in previews:
        print(p)

if __name__ == "__main__":
    asyncio.run(main())
