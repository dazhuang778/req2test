## ADDED Requirements

### Requirement: 解析三段式 MD 模板结构
系统 SHALL 解析符合固定三段式模板的 MD 文件，识别并提取三个顶层章节：`## 文档概述`、`## 规划功能`、`## 验收标准`。缺失任一章节时 SHALL 抛出明确错误提示。

#### Scenario: 成功解析完整三段式文档
- **WHEN** 输入的 MD 文件包含 `## 文档概述`、`## 规划功能`、`## 验收标准` 三个章节
- **THEN** 系统返回包含三部分文本内容的解析结果对象

#### Scenario: 文档缺少必要章节
- **WHEN** 输入的 MD 文件缺少 `## 规划功能` 章节
- **THEN** 系统抛出 `ParseError`，错误信息明确指出缺失的章节名

---

### Requirement: 提取 Mermaid 流程图块
系统 SHALL 从 `## 规划功能` 章节中提取所有 ` ```mermaid ` 代码块的原始文本内容（不含开闭标记）。

#### Scenario: 提取单个流程图
- **WHEN** `## 规划功能` 章节包含一个 mermaid 代码块
- **THEN** 解析结果的 `flowcharts` 列表包含该块的完整文本

#### Scenario: 提取多个流程图
- **WHEN** `## 规划功能` 章节包含多个 mermaid 代码块
- **THEN** 解析结果的 `flowcharts` 列表按文档顺序包含所有块的文本

#### Scenario: 无流程图时正常返回
- **WHEN** `## 规划功能` 章节不包含任何 mermaid 代码块
- **THEN** 解析结果的 `flowcharts` 为空列表，不报错

---

### Requirement: 提取规划功能章节中的功能设计文本
系统 SHALL 提取 `## 规划功能` 章节中除 mermaid 代码块以外的所有文本内容，作为功能设计描述。

#### Scenario: 提取混合内容中的功能文本
- **WHEN** `## 规划功能` 章节同时包含说明文字和 mermaid 代码块
- **THEN** `feature_text` 字段包含去除 mermaid 块后的剩余文本，保留原有格式（标题、列表等）

---

### Requirement: 支持按二级标题分块解析
系统 SHALL 支持将 MD 文件按二级标题（`##`）分块，返回块列表，用于处理大型文档时按块调用 LLM。

#### Scenario: 按章节分块
- **WHEN** 调用 `parse_sections()` 方法
- **THEN** 返回按 `##` 标题划分的 Section 列表，每个 Section 包含标题和内容
