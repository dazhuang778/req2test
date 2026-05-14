## ADDED Requirements

### Requirement: 为每个测试点生成五字段测试用例
系统 SHALL 对每个测试点独立调用 LLM，生成包含以下五个字段的测试用例：`id`（用例编号）、`title`（标题）、`preconditions`（前置条件）、`steps`（步骤）、`expected_result`（预期结果）。

#### Scenario: 单个测试点生成完整用例
- **WHEN** 传入测试点描述"正常账号密码登录"和模块前缀"LOGIN"、序号 1
- **THEN** 返回 `id="LOGIN-001"`、`title`、`preconditions`、`steps`、`expected_result` 均非空的测试用例对象

#### Scenario: 步骤字段为多步骤格式
- **WHEN** 生成登录相关测试用例
- **THEN** `steps` 字段包含编号步骤（如"1. 打开登录页\n2. 输入用户名"），不是单一字符串

---

### Requirement: 用例编号按模块分组递增
系统 SHALL 按 `{MODULE_PREFIX}-{序号三位数字}` 格式生成用例编号，序号从 001 起按测试点顺序递增，由调用方传入而非 LLM 生成，确保编号唯一且稳定。

#### Scenario: 编号格式正确
- **WHEN** 模块前缀为"LOGIN"，当前测试点为第 3 个
- **THEN** `id` 字段值为 `LOGIN-003`

#### Scenario: 序号超过 999 时正常处理
- **WHEN** 测试点超过 999 个
- **THEN** `id` 使用四位数字，如 `LOGIN-1000`，不截断

---

### Requirement: 批量生成时显示进度
系统 SHALL 在批量处理多个测试点时，通过 CLI 显示当前进度（已完成数 / 总数），支持用户感知进度。

#### Scenario: 进度实时更新
- **WHEN** 正在为第 3 个（共 10 个）测试点生成用例
- **THEN** 终端显示类似 `[3/10] 生成测试用例: 正常账号密码登录...`

---

### Requirement: 单个测试点失败不中断整体流程
系统 SHALL 对单个测试点的 LLM 调用独立处理异常；某测试点经 3 次重试仍失败时，SHALL 记录错误日志并跳过该测试点，继续处理其余测试点，最终在输出中标注跳过项。

#### Scenario: 单点失败跳过继续
- **WHEN** 第 3 个测试点连续 3 次调用失败
- **THEN** 输出 Excel 中不含该测试点的用例，且终端显示警告"测试点 [3] 生成失败，已跳过"

---

### Requirement: Pydantic 校验输出结构，失败重试
系统 SHALL 使用 Pydantic 模型校验每个测试用例的 LLM 输出；校验失败时将错误附加到 prompt 重试，最多 3 次。

#### Scenario: 缺失必要字段时重试
- **WHEN** LLM 返回的 JSON 缺少 `expected_result` 字段
- **THEN** Pydantic 校验失败，系统附带错误信息重新请求 LLM
