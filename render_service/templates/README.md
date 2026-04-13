# 模板目录

| 模板 Key | 名称 | LaTeX 母版 | 说明 |
|----------|------|-----------|------|
| `exam_paper` | 真题套卷 | 自身 | 完整套卷，考试封面 |
| `practice` | 刷题练习本 | exam_paper | 专项训练 / 自由组卷，练习封面 |
| `wrong_question` | 错题重刷 | exam_paper | 个性化错题本 |

所有模板共享 `exam_paper/main.tex.j2` 母版，通过 `manifest.toml` 中的 `template_source` 声明复用关系。
