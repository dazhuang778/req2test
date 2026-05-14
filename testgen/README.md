# testgen

从 MD 格式需求文档自动生成测试用例，导出为标准 Excel 文件的 CLI 工具。

## 特性

- 解析三段式 MD 模板（文档概述 / 规划功能 / 验收标准），支持内嵌 Mermaid 流程图
- 两段式生成：先展示测试点供确认，再生成完整五字段测试用例
- 测试点确认阶段支持多轮对话调整（用自然语言与 AI 沟通）
- 支持目录模式批量处理，每个 MD 文件独立输出 Excel
- 兼容所有 OpenAI 兼容接口（OpenAI / 通义千问 / 其他国内外供应商）
- Pydantic 校验 LLM 输出，失败自动重试

## 安装

```bash
cd testgen
pip install -e .
```

或直接安装依赖后以模块方式运行：

```bash
pip install -r requirements.txt
python -m testgen -i req.md -o cases.xlsx
```

## 配置

在**运行目录**创建 `config.yaml`（参考 `config.yaml.example`）：

```yaml
api_key: "sk-your-api-key"
model: "gpt-4o"
base_url: "https://api.openai.com/v1"

# 可选
# temperature: 0.2
# max_retries: 3
# timeout: 60
```

> 建议将 `config.yaml` 加入 `.gitignore`。  
> 也可通过环境变量覆盖 API Key：`export TESTGEN_API_KEY=sk-xxx`

## 使用

### 单文件模式

```bash
testgen -i requirements.md -o cases.xlsx
```

### 带额外上下文

```bash
testgen -i requirements.md -o cases.xlsx --context "重点关注安全场景和权限控制"
```

### 目录模式（批量处理）

```bash
testgen -i ./docs/ -o ./output/
```

`./docs/` 下每个 `.md` 文件将生成对应的 `./output/<文件名>_cases.xlsx`。

### 交互流程

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

  [1/7] 生成测试用例: 正常账号密码登录
  ...
✓ 导出完成: cases.xlsx  (7 条用例)
```

## 需求文档模板

```markdown
# 模块名称

## 文档概述
模块背景和整体说明...

## 规划功能

### 业务流程图
\`\`\`mermaid
flowchart TD
  A[开始] --> B{判断}
  ...
\`\`\`

### 具体功能设计
功能点详细说明...

## 验收标准
1. 验收条件一
2. 验收条件二
```

## 输出格式

Excel 文件每行一条测试用例，包含五列：

| 用例编号 | 标题 | 前置条件 | 步骤 | 预期结果 |
|---------|------|---------|------|---------|
| LOGIN-001 | 正常账号密码登录 | 用户已注册... | 1. 打开登录页... | 跳转首页... |
