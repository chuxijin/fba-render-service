#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试脚本：渲染汉语词汇手册模板示例并编译为 PDF。"""
import subprocess
import sys
import os
from pathlib import Path

# 强制 UTF-8 输出，避免 Windows GBK 编码问题
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 确保项目根目录在 sys.path 中
APP_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_ROOT))

from render_service.app.template_loader import render_template

# ─── 示例数据 ────────────────────────────────────────────────
SAMPLE_CONTEXT = {
    "book": {
        "title": "公务员考试汉语词汇积累",
        "subtitle": "高频成语与词语辨析 · 冲刺版",
    },
    "paper": {
        "sections": [
            {
                "title": "高频成语",
                "words": [
                    {
                        "name": "海市蜃楼",
                        "type": "成语",
                        "pinyin": "hǎi shì shèn lóu",
                        "baobian": "中性",
                        "structure": "联合式",
                        "definition_info": "蜃：大蛤蜊。原指海边或沙漠中，由于光线的折射和反射而出现的虚幻楼阁城郭。后比喻虚无缥缈的事物。",
                        "detail_means": {
                            "名词": ["比喻虚幻不实的事物或景象"],
                            "形容词": ["形容事物虚无缥缈、不可捉摸"],
                        },
                        "liju": [
                            "远处的绿洲不过是海市蜃楼，走近了才发现什么都没有。",
                            "他描绘的美好前景，最终被证明只是海市蜃楼。",
                            "沙漠中的海市蜃楼常常让旅行者迷失方向。",
                        ],
                        "synonyms": ["空中楼阁", "镜花水月", "虚无缥缈"],
                        "antonym": ["实实在在", "脚踏实地"],
                        "chu_chu": {"text": "《史记·天官书》", "source": "司马迁"},
                        "yin_zheng": {"text": "海旁蜃气象楼台，广野气成宫阙然。", "source": "《本草纲目·鳞部》"},
                        "frequency": 87,
                    },
                    {
                        "name": "画龙点睛",
                        "type": "成语",
                        "pinyin": "huà lóng diǎn jīng",
                        "baobian": "褒义",
                        "structure": "连动式",
                        "definition_info": "原形容梁代画家张僧繇作画的神妙。后比喻写文章或讲话时，在关键处用几句话点明实质，使内容更加生动传神。",
                        "detail_means": {
                            "动词": ["比喻在关键处加上精辟的话，使内容更加生动有力"],
                        },
                        "liju": [
                            "文章最后一段的议论起到了画龙点睛的作用。",
                            "这幅画添上那只飞鸟，真是画龙点睛之笔。",
                        ],
                        "synonyms": ["锦上添花", "点石成金"],
                        "antonym": ["画蛇添足", "弄巧成拙"],
                        "chu_chu": {"text": "唐·张彦远《历代名画记·张僧繇》", "source": ""},
                        "yin_zheng": {"text": "金陵安乐寺四白龙不点眼睛，每云：'点睛即飞去。'", "source": "《历代名画记》"},
                        "frequency": 65,
                    },
                    {
                        "name": "南辕北辙",
                        "type": "成语",
                        "pinyin": "nán yuán běi zhé",
                        "baobian": "贬义",
                        "structure": "联合式",
                        "definition_info": "心里想往南去，却驾车往北走。比喻行动和目的相反。",
                        "liju": [
                            "你这样做简直是南辕北辙，永远也达不到目的。",
                            "不改变方法，再努力也是南辕北辙。",
                        ],
                        "synonyms": ["背道而驰", "适得其反"],
                        "antonym": ["殊途同归", "如出一辙"],
                        "chu_chu": {"text": "《战国策·魏策四》", "source": ""},
                        "frequency": 53,
                    },
                    {
                        "name": "相得益彰",
                        "type": "成语",
                        "pinyin": "xiāng dé yì zhāng",
                        "baobian": "褒义",
                        "structure": "偏正式",
                        "definition_info": "指两个人或两件事物互相配合，双方的能力和作用更能显示出来。",
                        "detail_means": {
                            "动词": ["互相配合、互相补充，各自的长处表现得更加显著"],
                        },
                        "liju": [
                            "这两幅画挂在一起，相得益彰，更显艺术魅力。",
                            "他们的合作相得益彰，取得了出色的成果。",
                        ],
                        "synonyms": ["相辅相成", "珠联璧合"],
                        "antonym": ["势不两立", "两败俱伤"],
                        "chu_chu": {"text": "汉·王褒《圣主得贤臣颂》", "source": ""},
                        "frequency": 41,
                    },
                    {
                        "name": "望梅止渴",
                        "type": "成语",
                        "pinyin": "wàng méi zhǐ kě",
                        "baobian": "中性",
                        "structure": "连动式",
                        "definition_info": "原意是梅子酸，人想吃梅子就会流涎，因而止渴。后比喻愿望无法实现，用空想来安慰自己。",
                        "liju": [
                            "与其望梅止渴，不如脚踏实地去努力。",
                            "他这种做法不过是望梅止渴罢了。",
                        ],
                        "synonyms": ["画饼充饥", "聊以自慰"],
                        "antonym": ["脚踏实地"],
                        "chu_chu": {"text": "南朝宋·刘义庆《世说新语·假谲》", "source": ""},
                        "yin_zheng": {"text": "魏武行役，失汲道，三军皆渴，乃令曰：'前有大梅林，饶子，甘酸可以解渴。'士卒闻之，口皆出水，乘此得及前源。", "source": "《世说新语》"},
                        "frequency": 38,
                    },
                ],
            },
            {
                "title": "高频词语",
                "words": [
                    {
                        "name": "遏制",
                        "type": "动词",
                        "pinyin": "è zhì",
                        "baobian": "中性",
                        "definition_info": "制止；控制。用力阻止，使其不能发展或扩散。",
                        "detail_means": {
                            "动词": ["用力阻止、控制，使其不再扩展或蔓延"],
                        },
                        "liju": [
                            "政府采取了一系列措施来遏制通货膨胀。",
                            "必须坚决遏制腐败现象的蔓延。",
                        ],
                        "synonyms": ["遏止", "抑制", "制止"],
                        "antonym": ["放任", "纵容"],
                        "frequency": 72,
                    },
                    {
                        "name": "甄别",
                        "type": "动词",
                        "pinyin": "zhēn bié",
                        "baobian": "中性",
                        "definition_info": "鉴别，审察区分。仔细鉴别真假、好坏或优劣。",
                        "liju": [
                            "专家对文物进行了仔细甄别。",
                            "面对海量信息，我们需要有甄别真伪的能力。",
                        ],
                        "synonyms": ["鉴别", "辨别", "识别"],
                        "antonym": ["混淆", "混淆视听"],
                        "frequency": 45,
                    },
                    {
                        "name": "式微",
                        "type": "动词",
                        "pinyin": "shì wēi",
                        "baobian": "中性",
                        "definition_info": "指事物由兴盛到衰落。原为《诗经》篇名，后借指衰落、衰微。",
                        "liju": [
                            "随着互联网的兴起，传统书店日渐式微。",
                            "这门古老的手艺正面临式微的困境。",
                        ],
                        "synonyms": ["衰落", "衰微", "没落"],
                        "antonym": ["兴盛", "蓬勃", "鼎盛"],
                        "chu_chu": {"text": "《诗经·邶风·式微》", "source": ""},
                        "frequency": 33,
                    },
                ],
            },
        ],
    },
    "metadata": {
        "subject": "汉语",
        "motto": "千里之行，始于足下。",
    },
    "options": {
        "theme": "teal",
        "layout_mode": "standard",
    },
}


def main():
    # 渲染模板
    print("正在渲染模板...")
    manifest, variant, entrypoint, tex_source = render_template("hanyu", SAMPLE_CONTEXT)
    print(f"模板: {manifest.name} | 变体: {variant} | 入口: {entrypoint}")
    print(f"Tex 源码长度: {len(tex_source)} 字符")

    # 写出 tex 文件
    work_dir = APP_ROOT / "test_output"
    work_dir.mkdir(parents=True, exist_ok=True)
    tex_path = work_dir / "main_questions_only.tex"
    tex_path.write_text(tex_source, encoding="utf-8")
    print(f"已写入: {tex_path}")

    # 编译 PDF
    print("正在编译 PDF（xelatex）...")
    command = [
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-outdir={work_dir}",
        str(tex_path),
    ]
    result = subprocess.run(
        command, cwd=work_dir, capture_output=True, text=True, check=False, encoding="utf-8", errors="replace"
    )

    log_path = work_dir / "main_questions_only.log"
    log_path.write_text((result.stdout or "") + "\n" + (result.stderr or ""), encoding="utf-8")

    pdf_path = work_dir / "main_questions_only.pdf"
    if pdf_path.exists():
        print(f"✅ PDF 已生成: {pdf_path}")
        print(f"   大小: {pdf_path.stat().st_size / 1024:.1f} KB")
    else:
        print(f"❌ PDF 编译失败，日志: {log_path}")
        # 打印最后 30 行日志
        lines = (result.stdout + "\n" + result.stderr).strip().splitlines()
        for line in lines[-30:]:
            print(f"  {line}")

    # 同时渲染 combined_appendix 变体
    print("\n正在渲染 combined_appendix 变体...")
    context2 = dict(SAMPLE_CONTEXT)
    context2["render_variant"] = "combined_appendix"
    manifest2, variant2, entrypoint2, tex_source2 = render_template("hanyu", context2)
    tex_path2 = work_dir / "main_combined_appendix.tex"
    tex_path2.write_text(tex_source2, encoding="utf-8")
    print(f"已写入: {tex_path2}")

    print("正在编译 PDF（combined_appendix）...")
    command2 = [
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-outdir={work_dir}",
        str(tex_path2),
    ]
    result2 = subprocess.run(
        command2, cwd=work_dir, capture_output=True, text=True, check=False, encoding="utf-8", errors="replace"
    )

    log_path2 = work_dir / "main_combined_appendix.log"
    log_path2.write_text((result2.stdout or "") + "\n" + (result2.stderr or ""), encoding="utf-8")

    pdf_path2 = work_dir / "main_combined_appendix.pdf"
    if pdf_path2.exists():
        print(f"✅ PDF 已生成: {pdf_path2}")
        print(f"   大小: {pdf_path2.stat().st_size / 1024:.1f} KB")
    else:
        print(f"❌ PDF 编译失败，日志: {log_path2}")
        lines2 = (result2.stdout + "\n" + result2.stderr).strip().splitlines()
        for line in lines2[-30:]:
            print(f"  {line}")


if __name__ == "__main__":
    main()
