# Academic Research Daily

Academic Research Daily 是一个面向教育研究的自动化学术日报项目。项目会检索 OpenAlex 与 Crossref 中的英文教育期刊论文，按教育主题、SSCI 白名单、排除规则和历史记录进行筛选，再调用 DeepSeek 兼容接口生成中文精读摘要，最后输出 Markdown、Word 文档，并可通过邮箱发送日报。

本项目适合作为模板项目分享。别人下载、Fork 或使用模板创建新仓库后，通常只需要填写自己的配置，不需要修改 Python 代码。

## 功能概览

- 自动检索教育研究相关英文期刊论文。
- 支持 SSCI 白名单筛选，按期刊名和 ISSN 匹配。
- 支持历史去重，避免重复推荐同一篇论文。
- 默认关注 AI 教学、教师数字素养、教师专业发展、小学数学教育、教育技术等方向。
- 默认使用 DeepSeek 的 OpenAI 兼容接口。
- 自动生成中文结构化文献摘要。
- 输出 `daily/YYYY-MM-DD.md` 和 `daily/YYYY-MM-DD.docx`。
- 生成运行日志，便于排查错误。
- 支持本地运行和 GitHub Actions 自动运行。

## 快速使用

### 方式一：作为模板仓库使用

1. 点击仓库右上角的 `Use this template`，或直接 Fork 本仓库。
2. 进入自己新建的仓库。
3. 根据 `.env.example` 或 GitHub Actions 配置要求填写运行变量。
4. 打开 Actions，手动运行一次工作流。
5. 后续即可按计划自动运行。

### 方式二：本地运行

建议使用 Python 3.12。

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

复制配置模板：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，按 `.env.example` 填写自己的 AI 服务、邮箱和收件人配置。

检查配置：

```bash
python main.py check-config
```

运行一次并发送邮件：

```bash
python main.py run-once
```

只生成文件，不发送邮件：

```bash
python main.py run-once --no-email
```

## GitHub Actions 自动运行

工作流文件位于：

```text
.github/workflows/main.yml
```

它会完成以下流程：

1. 配置 Python 运行环境。
2. 安装依赖。
3. 运行测试。
4. 检查配置。
5. 执行日报生成程序。
6. 上传 `daily/`、`logs/` 和去重记录文件。

如果你使用 GitHub Actions，需要在仓库的 Actions 变量管理页面中填写自己的运行配置。字段名称可参考 `.env.example`。

进入路径：

```text
Settings → Secrets and variables → Actions
```

注意：这些配置只在当前仓库生效。如果别人 Fork 或 Use this template，需要在自己的仓库中重新填写。

## DeepSeek 说明

本项目默认使用 DeepSeek。由于 DeepSeek 使用 OpenAI 兼容接口格式，项目仍然使用 OpenAI Python SDK 调用模型。

也就是说，变量名称仍沿用 OpenAI 兼容写法，但实际默认接口已经指向 DeepSeek。

默认配置可查看：

```text
.env.example
config.py
```

如需更换模型，可修改 `.env` 或 GitHub Actions 中的模型配置。

## 邮箱发送说明

项目通过 SMTP 发送邮件。以 163 邮箱为例，需要先在邮箱网页版中开启 SMTP 服务，并生成客户端授权信息。

常见步骤：

1. 登录邮箱网页版。
2. 进入设置。
3. 找到 POP3、SMTP 或 IMAP 设置。
4. 开启 SMTP 服务。
5. 按提示生成客户端授权信息。
6. 将发件邮箱、授权信息和收件邮箱填入配置。

如果不想发送邮件，可以本地运行：

```bash
python main.py run-once --no-email
```

## 项目结构

```text
main.py
config.py
search.py
filter.py
summarizer.py
translator.py
mailer.py
html_generator.py
markdown_generator.py
logger.py
utils.py
requirements.txt
.env.example
.github/workflows/main.yml
templates/email.html.j2
tests/
daily/
logs/
data/
```

## 修改研究主题

检索关键词主要在：

```text
search.py
```

筛选关键词主要在：

```text
filter.py
```

常见可调整内容：

- 检索关键词。
- 保留关键词。
- 排除关键词。
- SSCI 筛选模式。
- 每次推送文献数量。
- 检索时间窗口。

## SSCI 白名单

默认白名单路径：

```text
data/ssci_whitelist_2026-06.xlsx
```

程序会尝试从表格中识别期刊名、ISSN、JIF、JCR 分区、CiteScore、出版社和学科分类。

筛选模式由 `SSCI_FILTER_MODE` 控制：

```text
strict  只保留白名单匹配论文
prefer  白名单论文优先，也允许非白名单相关论文
off     不使用白名单
```

## 输出文件

运行后通常会生成：

```text
daily/YYYY-MM-DD.md
daily/YYYY-MM-DD.docx
logs/today.log
logs/YYYY-MM-DD.log
data/seen_papers.json
```

`seen_papers.json` 用于记录已经推荐过的论文，避免重复推送。

## 常见问题

### 配置检查失败

先检查 `.env.example` 中要求的字段是否已经填写。如果是在 GitHub Actions 中运行，检查 Actions 配置页面是否已经填写同名字段。

### 邮件发不出去

检查 SMTP 服务是否开启、发件邮箱是否正确、客户端授权信息是否正确、收件邮箱是否填写。

### 没有检索到论文

可以尝试：

- 将 `SSCI_FILTER_MODE` 改为 `prefer`。
- 扩展 `search.py` 中的检索关键词。
- 调整检索时间窗口。
- 检查 OpenAlex 或 Crossref 是否临时限流。

### OpenAlex 配置是否必须填写

不是必须。项目不填写也可以检索。填写后可能更稳定。

## 分享前建议

如果你想让别人更方便地使用这个项目，建议在 GitHub 仓库设置中打开：

```text
Settings → General → Template repository
```

打开后，别人可以通过 `Use this template` 创建自己的副本，然后只填写自己的配置即可。

不要把本地 `.env` 文件提交到仓库。每个使用者都应该填写自己的配置。
