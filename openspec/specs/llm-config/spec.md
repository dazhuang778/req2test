# llm-config Specification

## Purpose
TBD - created by archiving change auto-testcase-generator. Update Purpose after archive.
## Requirements
### Requirement: 从 config.yaml 加载 LLM 连接参数
系统 SHALL 自动从当前工作目录查找 `config.yaml` 文件，读取 `api_key`、`model`、`base_url` 三个必填字段，用于初始化 OpenAI SDK 客户端。

#### Scenario: 成功加载完整配置
- **WHEN** 当前目录存在 `config.yaml`，包含三个必填字段
- **THEN** 系统使用该配置初始化 LLM 客户端，不报错

#### Scenario: config.yaml 不存在时报错
- **WHEN** 当前目录不存在 `config.yaml`
- **THEN** 系统输出 `Error: 未找到 config.yaml，请在当前目录创建配置文件。` 并退出，退出码非 0

#### Scenario: 缺少必填字段时报错
- **WHEN** `config.yaml` 存在但缺少 `api_key` 字段
- **THEN** 系统输出 `Error: config.yaml 缺少必填字段: api_key` 并退出，退出码非 0

---

### Requirement: 环境变量可覆盖 config.yaml 中的 api_key
系统 SHALL 优先使用环境变量 `TESTGEN_API_KEY` 的值作为 `api_key`，若环境变量已设置则忽略 `config.yaml` 中的 `api_key` 字段（不要求 config.yaml 中的 `api_key` 存在）。

#### Scenario: 环境变量优先于配置文件
- **WHEN** 环境变量 `TESTGEN_API_KEY=sk-env-key` 已设置，且 `config.yaml` 中 `api_key=sk-file-key`
- **THEN** 系统使用 `sk-env-key`，忽略配置文件中的值

#### Scenario: 环境变量未设置时回退到配置文件
- **WHEN** 环境变量 `TESTGEN_API_KEY` 未设置
- **THEN** 系统使用 `config.yaml` 中的 `api_key` 值

---

### Requirement: 提供 config.yaml 模板
系统 SHALL 在项目根目录提供 `config.yaml.example` 文件作为配置模板，包含所有字段的说明注释和示例值。

#### Scenario: 模板文件包含所有必填字段
- **WHEN** 查看 `config.yaml.example`
- **THEN** 文件包含 `api_key`、`model`、`base_url` 字段，每个字段有注释说明用途和示例值

---

### Requirement: 配置支持可选的 LLM 调用参数
系统 SHALL 支持 `config.yaml` 中的可选字段：`temperature`（默认 0.2）、`max_retries`（默认 3）、`timeout`（默认 60 秒）。

#### Scenario: 使用默认值时不需要配置可选字段
- **WHEN** `config.yaml` 只包含三个必填字段，无可选字段
- **THEN** 系统使用内置默认值正常运行

