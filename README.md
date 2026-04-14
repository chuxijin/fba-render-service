# render_pdf

独立的题本 PDF 渲染服务，为主业务系统提供高质量 PDF 输出能力。

- 使用 `Jinja2 + LaTeX + XeLaTeX/latexmk` 生成正式 PDF
- 推荐通过 Docker 部署，保证字体和 TeX 环境稳定
- 优先服务 `fba` 主后端，也可被其他系统调用

## 文档类参考

### 版式选项（`layout_mode`）

- `compact`：A4 紧凑版。题目间无任何空隙
- `standard`：A4 标准版。每个题目有一定空隙（大概 3cm 左右），每道题目的内容会强制在同一页，对于选择题而言，题目和选项不会跨业出现
- `loose`：A4 宽松版。每页会有 2 题，对于较长的题目，会自动占用一页
- `single`：A4 单题版。一页只会出现一题
- `pad_landscape`：横版 Pad 版。平板刷题，一页一题，适合小题（选择题和填空题）
- `pad_portrait`：竖版 Pad 版。平板刷题，一页一题，适合大题

> Pad 版固定纸面尺寸（横版 200×150mm、竖版 200×250mm），不受 `paper_size` 参数影响。

### 主题色（`theme`）

| 值 | 名称 | 色值 |
|---|------|------|
| `blue` | 蓝色 | `#1F4E79` |
| `green` | 绿色 | `#2E6A57` |
| `orange` | 橙色 | `#AF5A2A` |
| `purple` | 紫色 | `#6B4A8C` |
| `teal` | 青色 | `#01847C` |
| `crimson` | 红色 | `#8C2B2B` |
| `indigo` | 靛蓝 | `#38558F` |
| `amber` | 琥珀 | `#D58A05` |

### 其他选项

- `dark_mode`：暗色模式，暗底白字。Pad 版和电子阅读场景推荐
- `show_source`：显示题目来源标签
- `include_answer`：附带答案
- `include_analysis`：附带解析

### 渲染变体（`render_variant`）

- `questions_only`：仅题目
- `solutions_only`：仅解析
- `combined_inline`：题解合订（逐题附解析）
- `combined_appendix`：题解合订（解析置后）

### 封面类型（`cover_style`）

- `exam`：考试封面（仿真准考证栏、条形码区、注意事项）
- `practice`：练习封面（TikZ 色块设计、题本概览）

练习封面通过 `metadata` 支持以下可选字段：

| 字段 | 说明 | 默认值 |
|------|------|-------|
| `practice_cover_motto` | 封面座右铭 | 空（不显示） |
| `practice_cover_creator` | 制作人 | 空（不显示） |
| `practice_cover_update_time` | 更新时间 | 空（不显示） |
| `practice_cover_img` | 封面图片路径 | 空（不显示） |
| `practice_cover_kicker` | 顶部前置标题 | 模板名称 |
| `practice_cover_badge` | 右上角徽章 | 题本类型 |
| `practice_cover_footer` | 底部说明文案 | 自动生成描述 |

> Pad 版不显示封面。

### 纸张大小（`paper_size`）

仅在非 Pad 版式下生效：`A4`、`A5`、`B5`、`Letter`、`Legal`

### 水印（`watermark_text`）

通过 metadata 传入文字水印。传入非空字符串即启用。

## 目录结构

```text
render_pdf/
  README.md
  .gitignore
  deploy/
    render-book/
      Dockerfile
      docker-compose.yml
      .env.example
  render_service/
    requirements.txt
    app/
    templates/
    fonts/
    output/
    workdir/
```

## 启动建议

Docker 部署：

```bash
cd deploy/render-book
cp .env.example .env
docker compose up -d --build
```

## 当前内置模板

| 模板 key | 名称 | 说明 |
|---------|------|------|
| `exam_paper` | 真题套卷 | 母版模板，完整套卷 + 考试封面 |
| `practice` | 刷题练习本 | 专项训练 / 自由组卷 + 练习封面 |
| `wrong_question` | 错题重刷 | 个性化错题本 |

## 渲染协议

`POST /api/v1/render` 支持两层协议：

对外统一协议：

- `context.render_plan.content_mode`：`questions_only` / `questions_with_answers`
- `context.render_plan.answer_layout`：`inline` / `appendix`
- `context.render_plan.delivery_mode`：`single_pdf` / `split_pdf`

执行层内部协议：

- `render_variant`：`questions_only` / `solutions_only` / `combined_inline` / `combined_appendix`
- 如果不显式传入，服务按 `content_mode + answer_layout + delivery_mode` 推断

输出规则：

- 工作目录按 `job_id/render_variant/` 隔离
- 编译产物输出为 `output/{job_id}_{render_variant}.pdf`

下载产物接口：

- `GET /api/v1/jobs/{job_id}/artifacts/{render_variant}/pdf`
- `GET /api/v1/jobs/{job_id}/artifacts/{render_variant}/log`

## 模板复用机制

- 模板目录下的 `manifest.toml` 可通过 `template_source = "exam_paper"` 复用已有版式
- 业务题本类型和底层 LaTeX 版式解耦，新增题本时通常只需要补 manifest

## 富文本与图片处理

- 题干/选项/解析中的 HTML 在渲染阶段转换为可编译的 LaTeX 片段
- 远程图片优先下载到工作目录 `assets/`，通过 `\includegraphics` 内嵌到 PDF
- 不支持或下载失败的图片退化为占位提示，不中断整体任务

## 解析块样式

解析块使用 `tcolorbox` 环境，支持：

- 跨页断裂（`breakable`）
- 圆角边框（`arc=2pt`）
- 左侧主题色竖线（`leftrule=2.5pt`）
- 暗色模式下自动调整背景色
