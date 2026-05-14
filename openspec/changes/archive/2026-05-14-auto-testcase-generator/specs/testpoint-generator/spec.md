## ADDED Requirements

### Requirement: 从需求内容生成测试点列表
系统 SHALL 调用 LLM，将文档概述、Mermaid 流程图、功能设计文本、验收标准合并为 prompt，生成覆盖主流程、异常分支、边界条件的测试点列表。

#### Scenario: 成功生成测试点
- **WHEN** 提供有效的需求文本和流程图内容
- **THEN** LLM 返回包含 `module_name`、`module_prefix`、`test_points` 的 JSON，`test_points` 列表不为空

#### Scenario: 文档无流程图时仍能生成
- **WHEN** `flowcharts` 列表为空，仅有功能设计文本
- **THEN** 系统仍调用 LLM 生成测试点，prompt 中省略流程图部分

---

### Requirement: LLM 输出包含模块英文缩写前缀
系统 SHALL 在 prompt 中要求 LLM 为该模块推导一个英文大写缩写（如 `LOGIN`、`REGISTER`），作为 `module_prefix` 字段输出，用于后续用例编号。

#### Scenario: 中文模块名推导英文前缀
- **WHEN** 文档描述的模块名为"用户登录"
- **THEN** `module_prefix` 为合理的英文大写缩写（如 `LOGIN`），长度 3-10 个字符，仅含字母

---

### Requirement: Pydantic 校验输出结构，失败重试
系统 SHALL 使用 Pydantic 模型校验 LLM 返回的 JSON。校验失败时，SHALL 将错误详情附加到 prompt 重新请求，最多重试 3 次。超过重试次数后抛出 `LLMOutputError`。

#### Scenario: 首次校验成功
- **WHEN** LLM 返回格式正确的 JSON
- **THEN** 系统直接返回校验后的 Pydantic 对象，不触发重试

#### Scenario: 校验失败后重试成功
- **WHEN** LLM 第一次返回格式错误，第二次返回正确格式
- **THEN** 系统重试一次后返回正确结果，共调用 LLM 2 次

#### Scenario: 超出最大重试次数
- **WHEN** LLM 连续 3 次返回格式错误的 JSON
- **THEN** 系统抛出 `LLMOutputError`，错误信息包含最后一次的 Pydantic 校验错误详情

---

### Requirement: 输出标准化的测试点数据模型
系统 SHALL 返回符合以下结构的 Pydantic 模型：`module_name`（模块中文名）、`module_prefix`（英文大写缩写）、`test_points`（字符串列表，每项为一个测试点描述）。

#### Scenario: 数据模型字段完整性
- **WHEN** LLM 输出缺少 `module_prefix` 字段
- **THEN** Pydantic 校验失败，触发重试机制
