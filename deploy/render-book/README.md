# render-book Docker 环境

这是题本渲染服务的第一版容器化骨架，职责是：

- 挂载模板目录
- 挂载自定义字体目录
- 提供独立的 LaTeX 编译环境
- 输出 PDF 到宿主机目录

## 目录说明

```text
deploy/render-book/
  Dockerfile
  docker-compose.yml
  .env.example
  entrypoint.sh

render_service/
  app/
  templates/
  fonts/
  output/
  workdir/
```

## 启动方式

在仓库根目录执行：

```bash
cd deploy/render-book
cp .env.example .env
docker compose up -d --build
```

健康检查：

```bash
curl http://127.0.0.1:9000/healthz
```

最小渲染测试（先只渲染 `.tex`，不编 PDF）：

```bash
curl -X POST http://127.0.0.1:9000/api/v1/render \
  -H "Content-Type: application/json" \
  -d '{
    "template_key": "exam_paper",
    "compile_pdf": false,
    "context": {
      "book": {
        "title": "演示题本",
        "subtitle": "Docker 骨架联调"
      },
      "options": {
        "show_source": true,
        "include_answer": true,
        "include_analysis": false
      },
      "paper": {
        "sections": [
          {
            "title": "第一部分 言语理解",
            "questions": [
              {
                "stem_text": "下列说法正确的是？",
                "options": [
                  { "content_text": "选项A" },
                  { "content_text": "选项B" }
                ],
                "source_text": "2025 模拟题",
                "answer_text": "B"
              }
            ]
          }
        ]
      }
    }
  }'
```

## 与 FBA 主后端对接

如果主后端直接跑在宿主机上：

```env
RENDER_BOOK_EXECUTOR_MODE=external
RENDER_BOOK_EXECUTOR_URL=http://127.0.0.1:9000
```

如果未来把主后端也放进同一个 Docker 网络，再把地址改成容器服务名即可，例如：

```env
RENDER_BOOK_EXECUTOR_URL=http://render_book:9000
```

## 模板放在哪里

模板统一放在：

```text
render_service/templates/<template_key>/
```

例如：

```text
render_service/templates/exam_paper/
  manifest.toml
  main.tex.j2
```

## 自定义字体放在哪里

把字体文件放到：

```text
render_service/fonts/
```

容器启动时会刷新字体缓存，建议把你最终要用的中文字体固定在这里，不要依赖宿主机字体。

## 第一版说明

这一版先解决“环境稳定”和“目录规范”：

- 服务可独立启动
- 模板和字体路径固定
- 支持把 Jinja2 模板渲染成 `.tex`
- 支持调用 `latexmk -xelatex` 生成 PDF

下一步再接：

- FBA 主后端创建任务后真正调用该服务
- 模板参数协议与题库数据结构对齐
- 结果上传对象存储和任务状态回写
