## ADDED Requirements

### Requirement: 提供 testgen CLI 命令入口
系统 SHALL 通过 `testgen` 命令提供 CLI 入口，支持以下参数：
- `-i/--input`（必填）：单个 MD 文件路径，或包含 MD 文件的目录路径
- `-o/--output`（必填）：单文件模式下为输出 Excel 文件路径；目录模式下为输出目录路径
- `--context`（可选）：额外上下文说明字符串，注入所有 LLM prompt

#### Scenario: 单文件基本调用成功
- **WHEN** 执行 `testgen -i requirements.md -o cases.xlsx`
- **THEN** 工具完整执行解析 → 生成测试点 → 用户确认/对话 → 生成用例 → 导出流程

#### Scenario: 带额外上下文调用
- **WHEN** 执行 `testgen -i req.md -o cases.xlsx --context "重点关注安全场景和权限控制"`
- **THEN** 该上下文字符串注入 Pass 1 的 system prompt，LLM 生成测试点时优先覆盖安全相关场景

#### Scenario: 缺少必填参数时提示用法
- **WHEN** 执行 `testgen -o cases.xlsx`（缺少 `-i` 参数）
- **THEN** 终端输出 Click 的标准错误提示，包含缺少参数名和使用说明，退出码非 0

#### Scenario: 输入路径不存在时报错
- **WHEN** `-i` 指定的文件或目录路径不存在
- **THEN** 终端输出 `Error: 路径不存在: <path>`，退出码非 0

---

### Requirement: 支持目录模式批量处理
系统 SHALL 在 `-i` 指定路径为目录时，自动扫描该目录下所有 `.md` 文件（不递归子目录），按文件名顺序依次处理每个文件，各自输出到 `-o` 指定目录下的 `{原文件名}_cases.xlsx`。

#### Scenario: 目录模式处理多个文件
- **WHEN** 执行 `testgen -i ./docs/ -o ./output/`，`./docs/` 下有 `login.md` 和 `register.md`
- **THEN** 依次处理两个文件，分别生成 `./output/login_cases.xlsx` 和 `./output/register_cases.xlsx`

#### Scenario: 目录模式下输出目录不存在时自动创建
- **WHEN** `-o` 指定的目录不存在
- **THEN** 系统自动创建该目录，不报错

#### Scenario: 目录中无 MD 文件时报错
- **WHEN** `-i` 指定的目录存在但不含任何 `.md` 文件
- **THEN** 终端输出 `Error: 目录中未找到 .md 文件: <path>`，退出码非 0

#### Scenario: 目录模式下单文件失败继续处理
- **WHEN** 处理 `login.md` 时 LLM 调用失败，`register.md` 正常
- **THEN** 跳过 `login.md`，继续处理 `register.md`，结束时显示汇总：`完成 1/2，失败 1/2: login.md`

#### Scenario: 目录模式开始时显示文件列表
- **WHEN** 目录模式启动
- **THEN** 终端首先列出待处理的文件列表和总数，格式如：`发现 3 个 MD 文件，开始处理...`

---

### Requirement: 展示解析和生成进度
系统 SHALL 在关键步骤输出状态提示，格式为 `✓ <步骤描述>` 表示完成，`正在<步骤描述>...` 表示进行中。目录模式下 SHALL 在每个文件前显示文件序号和名称。

#### Scenario: 单文件模式进度输出
- **WHEN** 工具正常执行完整流程
- **THEN** 终端依次输出：`正在解析文档...` → `✓ 文档解析完成` → `正在生成测试点...` → 测试点列表 → 确认/对话提示 → `[N/M] 生成测试用例: <测试点>` → `✓ 导出完成: <output路径>`

#### Scenario: 目录模式进度输出
- **WHEN** 目录模式处理第 2 个文件（共 3 个）
- **THEN** 终端输出类似 `[2/3] 处理: login.md` 的文件标题，随后是该文件的标准流程输出

---

### Requirement: 测试点确认阶段支持多轮对话调整
系统 SHALL 在 Pass 1 展示测试点后，进入三态交互循环：
- 用户输入 `y` 或直接回车 → 确认，进入 Pass 2
- 用户输入 `n` → 取消当前文件处理
- 用户输入其他任何文字 → 视为对话消息，发送给 LLM 调整测试点，重新展示更新后的列表，继续等待输入

对话历史 SHALL 以完整 messages 数组维护，包含 system prompt、原始文档内容和所有历史轮次，确保 LLM 有完整上下文。

#### Scenario: 用户确认继续
- **WHEN** 系统展示测试点列表后，用户输入 `y` 或直接回车
- **THEN** 系统继续执行 Pass 2 生成测试用例

#### Scenario: 用户拒绝继续
- **WHEN** 系统展示测试点列表后，用户输入 `n`
- **THEN** 系统输出 `已取消。` 并跳过当前文件（单文件模式则退出，目录模式继续下一文件）

#### Scenario: 用户通过对话调整测试点
- **WHEN** 系统展示测试点后，用户输入 `增加关于验证码失效的测试场景`
- **THEN** 系统将该消息追加到对话历史，调用 LLM 重新生成测试点列表，展示更新后的列表，并再次等待输入

#### Scenario: 多轮对话后确认
- **WHEN** 用户经过 2 轮对话调整后输入 `y`
- **THEN** 系统使用最新一轮的测试点列表进入 Pass 2

#### Scenario: 测试点展示格式（含操作提示）
- **WHEN** 生成或更新了测试点列表
- **THEN** 终端输出格式如下：
  ```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  模块: 用户登录 [LOGIN]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 正常账号密码登录
  2. 错误密码处理
  ...
  共 5 个测试点
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [y] 确认并生成测试用例  [n] 取消  [或输入说明与 AI 对话调整]:
  ```

---

### Requirement: 输出文件已存在时给出覆盖提示
系统 SHALL 在写入 Excel 前检查目标文件是否存在，存在时在终端输出提示 `注意: <path> 已存在，将被覆盖。`，然后继续执行，不打断流程。

#### Scenario: 文件存在时给出提示
- **WHEN** 目标 `cases.xlsx` 已存在，用户已通过测试点确认
- **THEN** 终端输出覆盖提示后继续写入，不要求用户再次确认

---

### Requirement: LLM 调用失败时输出明确错误
系统 SHALL 在 LLM 调用返回 HTTP 错误（如 401 / 429 / 500）时，捕获异常并输出人类可读的错误信息，包含状态码和建议操作，退出码非 0。

#### Scenario: API Key 无效时报错
- **WHEN** config.yaml 中的 `api_key` 无效，LLM 返回 401
- **THEN** 终端输出 `Error: API 认证失败 (401)，请检查 config.yaml 中的 api_key`，工具退出
