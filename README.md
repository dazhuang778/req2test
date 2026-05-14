# req2test

从 Markdown 需求文档自动生成测试点和测试用例，导出为标准 Excel 文件的 LLM CLI 工具。

## 功能特性

- **两段式生成**：先生成测试点列表供确认，再批量生成完整测试用例
- **多轮对话调整**：测试点确认阶段可用自然语言与 AI 对话，随时修改
- **支持 Mermaid 流程图**：自动提取需求文档中的业务流程图辅助生成
- **目录批量处理**：一次处理整个目录，每个 MD 文件独立输出 Excel
- **结果自动保存**：同步输出测试点文本文件和测试用例 Excel
- **兼容多种 LLM**：支持所有 OpenAI 兼容接口（OpenAI、国内各大供应商等）
- **健壮的解析**：使用 json-repair 自动修复 LLM 输出的 JSON 格式错误

## 目录结构

```
req2test/
├── testgen/                # CLI 工具源码
│   ├── testgen/
│   │   ├── __main__.py     # CLI 入口
│   │   ├── parser.py       # MD 文档解析
│   │   ├── generator.py    # LLM 调用与生成逻辑
│   │   ├── models.py       # Pydantic 数据模型
│   │   ├── exporter.py     # Excel 导出
│   │   └── config.py       # 配置加载
│   ├── config.yaml.example # 配置文件模板
│   ├── requirements.txt
│   └── pyproject.toml
└── openspec/               # 项目变更规格文档
```

## 安装

```bash
cd testgen
pip install -r requirements.txt
pip install -e .
```

安装后可直接使用 `testgen` 命令；或不安装直接用 `python -m testgen`。

## 配置

在**运行目录**下创建 `config.yaml`（参考 `testgen/config.yaml.example`）：

```yaml
api_key: "sk-your-api-key"
model: "gpt-4o"
base_url: "https://api.openai.com/v1"

# 可选参数（以下为默认值）
# temperature: 0.2
# max_retries: 3
# timeout: 60
```

也可通过环境变量覆盖 API Key：

```bash
export TESTGEN_API_KEY=sk-xxx
```

> **注意**：`config.yaml` 含有 API Key，已加入 `.gitignore`，请勿提交。

## 使用方法

### 单文件模式

```bash
testgen -i requirements.md -o output/cases.xlsx
```

### 目录批量模式

```bash
testgen -i ./docs/ -o ./output/
```

`docs/` 下每个 `.md` 文件生成对应的 `output/<文件名>_cases.xlsx` 和 `output/<文件名>_cases_points.txt`。

### 附加上下文说明

通过 `--context` 向 LLM 注入额外指令，引导生成方向：

```bash
testgen -i requirements.md -o cases.xlsx --context "重点关注安全场景和异常分支"
```

## 交互流程

```
正在解析文档...
✓ 文档解析完成
正在生成测试点...
✓ 测试点生成完成

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
模块: 用户登录 [LOGIN]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 正常账号密码登录
  2. 错误密码处理
  3. 账号锁定机制
  ...

共 6 个测试点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[y] 确认并生成测试用例  [n] 取消  [或输入说明与 AI 对话调整]: 增加验证码相关场景

正在根据您的说明调整测试点...
（重新展示更新后的列表）

[y] 确认并生成测试用例  [n] 取消  [或输入说明与 AI 对话调整]: y

正在生成测试用例（共 7 个测试点）...
  [1/7] 生成测试用例: 正常账号密码登录
  [2/7] 生成测试用例: 错误密码处理
  ...
✓ 导出完成: cases.xlsx  (7 条用例)
✓ 测试点已保存: cases_points.txt  (7 个测试点)
```

确认阶段有三种输入：
| 输入 | 效果 |
|------|------|
| `y` 或直接回车 | 确认当前测试点，开始生成测试用例 |
| `n` | 取消，退出 |
| 任意说明文字 | 发送给 AI 调整测试点，循环直到满意 |

## 需求文档模板

工具要求 MD 文档包含以下三个章节（支持数字编号前缀，如 `1. 文档概述`）：

```markdown
# 模块名称

## 文档概述

模块背景和整体说明...

## 规划功能

### 业务流程图

​```mermaid
flowchart TD
  A[开始] --> B{判断条件}
  B -->|是| C[执行操作]
  B -->|否| D[结束]
​```

### 功能设计

具体功能点说明...

## 验收标准

1. 验收条件一
2. 验收条件二
```

## 输出格式

### Excel 测试用例（`cases.xlsx`）

每行一条测试用例，包含五列：

| 用例编号 | 标题 | 前置条件 | 步骤 | 预期结果 |
|---------|------|---------|------|---------|
| LOGIN-001 | 正常账号密码登录 | 用户已注册账号... | 1. 打开登录页面<br>2. 输入账号密码<br>3. 点击登录 | 成功跳转首页... |
| LOGIN-002 | 错误密码登录 | 同上 | 1. 输入错误密码<br>2. 点击登录 | 提示"密码错误"... |

### 测试点文件（`cases_points.txt`）

```
模块: 用户登录 [LOGIN]

1. 正常账号密码登录
2. 错误密码处理
3. 账号锁定机制
...
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `-i / --input` | ✓ | 输入的 MD 文件或目录路径 |
| `-o / --output` | ✓ | 输出的 Excel 文件路径（单文件模式）或目录（目录模式） |
| `--context` | | 额外上下文说明，注入 LLM prompt |
