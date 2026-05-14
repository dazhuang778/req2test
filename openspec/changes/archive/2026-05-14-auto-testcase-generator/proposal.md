## Why

测试人员手动分析需求文档、编写测试用例效率低且容易遗漏场景。通过 LLM 自动解析 MD 格式需求文档（含 Mermaid 流程图），两段式生成测试点和测试用例，并导出为标准 Excel 格式，可大幅提升测试设计效率和覆盖率。

## What Changes

- 新增 `testgen` CLI 工具，接受单个 MD 文件或目录作为输入，输出测试用例 Excel 文件
- 支持目录模式：自动扫描目录下所有 `.md` 文件，每个文件独立生成对应的 Excel 文件
- 支持解析固定三段式 MD 模板（文档概述 / 规划功能 / 验收标准），提取 Mermaid 流程图和功能设计文本
- 两段式 LLM 调用：先生成测试点（展示给用户确认），再批量生成完整测试用例
- 测试点确认阶段支持多轮对话：用户可用自然语言与 LLM 对话调整测试点，满意后再确认生成用例
- 支持 `--context` 参数预注入额外上下文（如"重点关注安全场景"），辅助 LLM 生成更有针对性的测试用例
- 测试用例包含：用例编号（按模块分组，如 LOGIN-001）、标题、前置条件、步骤、预期结果
- LLM 可配置（API Key / model name / base_url），兼容所有 OpenAI 兼容接口
- Pydantic 校验 LLM 输出结构，失败自动重试（最多 3 次）
- 导出标准 Excel 文件，每行一条测试用例

## Capabilities

### New Capabilities

- `md-parser`: 解析三段式 MD 模板，提取文档概述、Mermaid 流程图块、功能设计文本、验收标准
- `testpoint-generator`: 调用 LLM 从需求文本 + 流程图生成测试点列表，包含模块名推导英文缩写前缀
- `testcase-generator`: 为每个测试点调用 LLM 生成完整测试用例（五字段），带 Pydantic 校验和重试
- `excel-exporter`: 将结构化测试用例列表写入格式化 Excel 文件
- `cli-interface`: Click CLI 入口，实现 `-i / -o / --context` 参数、目录批量处理、进度展示、测试点确认与多轮对话调整
- `llm-config`: 从当前目录 `config.yaml` 加载 API Key / model / base_url 配置

### Modified Capabilities

## Impact

- 新增独立 Python 项目，无需修改现有代码
- 外部依赖：`openai`, `pydantic`, `openpyxl`, `click`, `pyyaml`
- 需要 Python 3.10+
- LLM API 调用产生费用，取决于文档长度和测试点数量
