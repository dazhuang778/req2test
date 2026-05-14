## ADDED Requirements

### Requirement: 导出测试用例到 Excel 文件
系统 SHALL 将测试用例列表写入 `.xlsx` 文件，每行一个测试用例，包含五列：用例编号、标题、前置条件、步骤、预期结果。列顺序 SHALL 固定为该顺序。

#### Scenario: 成功导出非空测试用例列表
- **WHEN** 传入 10 个测试用例对象，输出路径为 `cases.xlsx`
- **THEN** 生成的 Excel 文件包含 1 行表头 + 10 行数据，共 5 列

#### Scenario: 输出路径不存在时自动创建目录
- **WHEN** 输出路径为 `./output/cases.xlsx`，`output/` 目录不存在
- **THEN** 系统自动创建目录并写入文件，不报错

---

### Requirement: Excel 表头格式化
系统 SHALL 为表头行设置加粗样式和背景色（浅灰色 `#D9D9D9`），以区分表头和数据行。列宽 SHALL 根据内容类型自动适配：用例编号列宽 15，标题列宽 30，其余列宽 40。

#### Scenario: 表头样式正确应用
- **WHEN** 生成 Excel 文件
- **THEN** 第一行的字体为粗体，背景色为 `#D9D9D9`

---

### Requirement: 步骤和预期结果字段启用自动换行
系统 SHALL 对"步骤"和"预期结果"列的单元格启用文字自动换行（wrap_text），以完整显示多步骤内容。

#### Scenario: 多步骤内容正确换行显示
- **WHEN** 步骤字段包含 `\n` 分隔的多个步骤
- **THEN** Excel 单元格内容按换行符分行显示，不压缩成一行

---

### Requirement: 导出文件名冲突时覆盖写入
系统 SHALL 在目标文件已存在时直接覆盖，不弹出交互确认。CLI 层在写入前 SHALL 提示用户文件将被覆盖。

#### Scenario: 覆盖已存在的文件
- **WHEN** 目标路径 `cases.xlsx` 已存在
- **THEN** 文件被覆盖写入，原文件内容丢失，不抛出错误
