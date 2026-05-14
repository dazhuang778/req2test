## 1. 项目初始化

- [x] 1.1 创建项目目录结构：`testgen/` 包含 `__main__.py`、`parser.py`、`generator.py`、`models.py`、`exporter.py`、`config.py`
- [x] 1.2 创建 `requirements.txt`，添加依赖：`openai`、`pydantic>=2.0`、`openpyxl`、`click`、`pyyaml`
- [x] 1.3 创建 `config.yaml.example`，包含 `api_key`、`model`、`base_url`、`temperature`、`max_retries`、`timeout` 字段及注释说明
- [x] 1.4 配置 `setup.py` 或 `pyproject.toml`，注册 `testgen` 为 CLI 命令入口点

## 2. 配置加载模块（config.py）

- [x] 2.1 实现从当前目录自动查找并加载 `config.yaml` 的函数
- [x] 2.2 实现环境变量 `TESTGEN_API_KEY` 覆盖 `api_key` 的逻辑
- [x] 2.3 实现必填字段（`api_key`、`model`、`base_url`）缺失时的明确错误提示
- [x] 2.4 实现可选字段默认值：`temperature=0.2`、`max_retries=3`、`timeout=60`
- [x] 2.5 实现 `config.yaml` 文件不存在时的错误提示和退出

## 3. MD 解析模块（parser.py）

- [x] 3.1 实现按 `## 文档概述`、`## 规划功能`、`## 验收标准` 标题分割 MD 文档的函数
- [x] 3.2 实现缺少必要章节时抛出 `ParseError` 的校验逻辑
- [x] 3.3 实现从"规划功能"章节提取所有 ` ```mermaid ` 代码块文本的函数（正则实现）
- [x] 3.4 实现从"规划功能"章节去除 mermaid 块后提取功能设计文本的函数
- [x] 3.5 实现 `parse_sections()` 方法，按二级标题 `##` 分块返回 Section 列表

## 4. Pydantic 数据模型（models.py）

- [x] 4.1 定义 `TestPointResult` 模型：`module_name: str`、`module_prefix: str`、`test_points: list[str]`
- [x] 4.2 添加 `module_prefix` 字段的 validator：仅含大写字母，长度 3-10
- [x] 4.3 定义 `TestCase` 模型：`id: str`、`title: str`、`preconditions: str`、`steps: str`、`expected_result: str`
- [x] 4.4 定义 `TestCaseBatch` 模型：`test_cases: list[TestCase]`（用于批量解析 LLM 输出）

## 5. LLM 调用与测试点生成（generator.py - Pass 1）

- [x] 5.1 实现 LLM 客户端初始化函数，使用 `openai.OpenAI(api_key=..., base_url=...)`
- [x] 5.2 编写 Pass 1 的 system prompt 和 user prompt 模板：输入文档概述 + 流程图 + 功能设计 + 验收标准，要求输出 JSON 格式测试点列表和模块前缀
- [x] 5.3 实现 Pydantic 校验 + 重试机制的通用函数 `call_with_retry(prompt, model_cls, max_retries)`
- [x] 5.4 实现 `generate_test_points(parsed_doc, config)` 函数，调用 Pass 1 返回 `TestPointResult`
- [x] 5.5 实现流程图为空时的 prompt 降级处理（省略流程图部分）

## 6. 测试用例生成（generator.py - Pass 2）

- [x] 6.1 编写 Pass 2 的 prompt 模板：输入单个测试点描述 + 模块上下文，要求输出五字段 JSON
- [x] 6.2 实现 `generate_test_case(test_point, index, module_prefix, config)` 函数，生成单个 `TestCase`
- [x] 6.3 实现用例编号格式化逻辑：`{MODULE_PREFIX}-{index:03d}`，超过 999 时自动扩展位数
- [x] 6.4 实现批量生成函数 `generate_all_cases(test_points, module_prefix, config)`，含进度输出 `[N/M]`
- [x] 6.5 实现单个测试点失败后跳过并记录警告、继续处理其余测试点的逻辑

## 7. Excel 导出模块（exporter.py）

- [x] 7.1 实现 `export_to_excel(test_cases, output_path)` 函数，使用 `openpyxl` 写入五列数据
- [x] 7.2 实现表头行：列名为"用例编号/标题/前置条件/步骤/预期结果"，加粗 + 背景色 `#D9D9D9`
- [x] 7.3 实现列宽设置：用例编号 15，标题 30，其余三列各 40
- [x] 7.4 实现"步骤"和"预期结果"列的 `wrap_text=True` 自动换行
- [x] 7.5 实现输出目录不存在时自动创建的逻辑

## 8. CLI 入口（__main__.py）

- [x] 8.1 使用 `click` 定义 `testgen` 命令，添加 `-i/--input`、`-o/--output` 必填参数和 `--context` 可选参数
- [x] 8.2 实现输入路径检测：判断 `-i` 为文件还是目录，路径不存在时报错退出
- [x] 8.3 实现单文件模式执行流程串联：加载配置 → 解析 MD → Pass 1 → 展示测试点 → 多轮对话/确认 → Pass 2 → 导出 Excel
- [x] 8.4 实现目录模式：扫描 `.md` 文件列表 → 显示文件总数 → 顺序处理每个文件 → 结束时显示成功/失败汇总
- [x] 8.5 实现目录模式下单文件失败跳过并记录，不中断整体流程
- [x] 8.6 实现多轮对话确认交互：格式化展示测试点，三态输入（`y`/`n`/对话消息），循环直到确认或取消
- [x] 8.7 实现对话消息处理：将用户输入追加到 messages 历史，调用 LLM 重新生成测试点，刷新展示
- [x] 8.8 实现 `--context` 参数注入 Pass 1 system prompt 的逻辑（单文件和目录模式均生效）
- [x] 8.9 实现输出文件已存在时的覆盖提示（不阻断流程）
- [x] 8.10 实现关键步骤的进度输出：`正在<步骤>...` 和 `✓ <步骤完成>` 格式，目录模式显示 `[N/M] 处理: <文件名>`
- [x] 8.11 实现 LLM HTTP 错误的捕获和人类可读错误提示（401/429/500 等）

## 9. 集成测试与验证

- [x] 9.1 使用示例 MD 文件（含 mermaid 流程图）端到端测试单文件完整流程
- [x] 9.2 测试目录模式：含 3 个 MD 文件的目录，验证各自输出独立 Excel 文件
- [x] 9.3 测试多轮对话流程：验证 2 轮对话调整后确认，输出使用最新测试点
- [x] 9.4 测试 `--context` 参数：验证上下文字符串出现在 LLM 请求的 system prompt 中
- [x] 9.5 验证 Excel 输出格式：列宽、表头样式、换行、编号格式
- [x] 9.6 验证重试机制：mock LLM 返回错误 JSON，确认最多重试 3 次
- [x] 9.7 验证错误场景：缺少 config.yaml、API Key 无效、MD 缺少章节、目录无 MD 文件
- [x] 9.8 更新 `README.md`，包含安装步骤、config.yaml 配置说明、单文件和目录模式使用示例、`--context` 用法
