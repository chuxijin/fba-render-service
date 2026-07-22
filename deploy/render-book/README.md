# render-book 宿主机部署

题本渲染服务直接运行在云服务器宿主机。模板由 FBA 后端仓库统一管理，渲染服务通过环境变量读取只读模板目录。

## 目录说明

```text
deploy/render-book/
  Dockerfile
  docker-compose.yml
  .env.example
  render-book.service.example
  entrypoint.sh

render_service/
  app/
  fonts/
  output/
  workdir/
```

## systemd 启动

创建 `/etc/fba-render-book.env`：

```env
RENDER_SERVICE_TEMPLATES_ROOT=/srv/fba/backend/plugin/render_book/templates
RENDER_SERVICE_FONTS_ROOT=/srv/render_pdf/render_service/fonts
RENDER_SERVICE_OUTPUT_ROOT=/srv/render_pdf/render_service/output
RENDER_SERVICE_WORK_ROOT=/srv/render_pdf/render_service/workdir
RENDER_SERVICE_COMPILE_ENABLED=true
```

复制 `render-book.service.example` 到 `/etc/systemd/system/render-book.service`，并按实际运行用户、项目目录修改 `User`、`Group`、`WorkingDirectory`、`ExecStart`。然后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now render-book
sudo systemctl status render-book
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

## 模板目录

模板源码统一由 FBA 管理：

```text
fba/backend/plugin/render_book/templates/<template_key>/<version>/
```

宿主机服务通过以下环境变量读取：

```env
RENDER_SERVICE_TEMPLATES_ROOT=/srv/fba/backend/plugin/render_book/templates
```

发布新模板版本后，应同时重启 FBA 后端和 `render-book` 服务，使两端重新扫描模板清单；已发布版本目录不可原地修改。

## 自定义字体放在哪里

把字体文件放到：

```text
render_service/fonts/
```

请在宿主机安装或固定需要的中文字体，并确认运行 `render-book` 的用户具备读取权限。
