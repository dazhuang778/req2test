import json
from typing import TypeVar, Type

from json_repair import repair_json
from openai import OpenAI, APIStatusError
from pydantic import BaseModel, ValidationError

from .config import Config
from .models import TestPointResult, TestCase, TestCaseBatch
from .parser import ParsedDoc

T = TypeVar("T", bound=BaseModel)

_PASS1_SYSTEM = """\
你是一名专业的软件测试工程师。根据提供的需求文档，生成完整的测试点列表。
要求：
1. 覆盖主流程、异常分支、边界条件
2. 为该模块推导一个英文大写缩写作为 module_prefix（3-10个大写字母，如 LOGIN、REGISTER）
3. 严格按照以下 JSON 格式输出，不要有任何额外文字：
{
  "module_name": "模块中文名",
  "module_prefix": "MODULE",
  "test_points": [
    "测试点描述1",
    "测试点描述2"
  ]
}
"""

_PASS2_SYSTEM = """\
你是一名专业的软件测试工程师。根据测试点生成详细的测试用例。
严格按照以下 JSON 格式输出，不要有任何额外文字：
{
  "id": "PREFIX-001",
  "title": "测试用例标题",
  "preconditions": "前置条件描述",
  "steps": "1. 步骤一\\n2. 步骤二\\n3. 步骤三",
  "expected_result": "预期结果描述"
}
"""

_REFINE_SYSTEM = """\
你是一名专业的软件测试工程师。根据用户的反馈调整测试点列表。
严格按照以下 JSON 格式输出，不要有任何额外文字：
{
  "module_name": "模块中文名",
  "module_prefix": "MODULE",
  "test_points": [
    "测试点描述1",
    "测试点描述2"
  ]
}
"""


def _strip_code_fence(text: str) -> str:
    """剥离 markdown 代码块并提取最外层 JSON 对象。"""
    text = text.strip()
    # 去除 ```json ... ``` 包裹
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if "```" in text:
            text = text[: text.rfind("```")]
    text = text.strip()
    # 提取第一个完整的 {...} JSON 对象（处理前后多余文字）
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return text


def _build_client(config: Config) -> OpenAI:
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
    )


def _call_with_retry(
    client: OpenAI,
    messages: list[dict],
    model_cls: Type[T],
    config: Config,
) -> T:
    last_error: str = ""
    for attempt in range(config.max_retries):
        msgs = list(messages)
        if last_error and attempt > 0:
            msgs.append({
                "role": "user",
                "content": f"你上次的输出格式有误，请修正并重新输出。错误详情：{last_error}",
            })

        response = client.chat.completions.create(
            model=config.model,
            messages=msgs,
            temperature=config.temperature,
        )
        raw = _strip_code_fence(response.choices[0].message.content or "")

        try:
            repaired = repair_json(raw, return_objects=False)
            return model_cls.model_validate_json(repaired)
        except (ValidationError, json.JSONDecodeError) as e:
            last_error = str(e)

    raise RuntimeError(
        f"LLM 输出校验连续失败 {config.max_retries} 次。最后错误：{last_error}"
    )


def generate_test_points(
    doc: ParsedDoc,
    config: Config,
    context: str = "",
    conversation_history: list[dict] | None = None,
) -> tuple[TestPointResult, list[dict]]:
    """Pass 1: 生成测试点。返回结果和完整 messages 历史（供后续多轮对话使用）。"""
    client = _build_client(config)

    system_content = _PASS1_SYSTEM
    if context:
        system_content += f"\n\n额外要求：{context}"

    if conversation_history:
        messages = conversation_history
    else:
        user_content = _build_pass1_user_content(doc)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    result = _call_with_retry(client, messages, TestPointResult, config)

    messages.append({
        "role": "assistant",
        "content": result.model_dump_json(),
    })
    return result, messages


def refine_test_points(
    user_message: str,
    messages: list[dict],
    config: Config,
) -> tuple[TestPointResult, list[dict]]:
    """多轮对话：根据用户反馈重新生成测试点。"""
    client = _build_client(config)

    messages = list(messages)
    messages[0] = {"role": "system", "content": _REFINE_SYSTEM}
    messages.append({"role": "user", "content": user_message})

    result = _call_with_retry(client, messages, TestPointResult, config)
    messages.append({
        "role": "assistant",
        "content": result.model_dump_json(),
    })
    return result, messages


def generate_test_case(
    test_point: str,
    index: int,
    module_prefix: str,
    doc: ParsedDoc,
    config: Config,
) -> TestCase:
    """Pass 2: 为单个测试点生成测试用例。"""
    client = _build_client(config)

    case_id = _format_id(module_prefix, index)
    user_content = (
        f"模块：{module_prefix}\n"
        f"用例编号：{case_id}\n"
        f"测试点：{test_point}\n\n"
        f"功能背景：\n{doc.feature_text}\n\n"
        f"验收标准：\n{doc.acceptance}"
    )

    messages = [
        {"role": "system", "content": _PASS2_SYSTEM},
        {"role": "user", "content": user_content},
    ]
    result = _call_with_retry(client, messages, TestCase, config)
    result.id = case_id
    return result


def generate_all_cases(
    test_points: list[str],
    module_prefix: str,
    doc: ParsedDoc,
    config: Config,
    on_progress=None,
) -> tuple[list[TestCase], list[str]]:
    """批量生成测试用例。返回 (成功列表, 失败测试点列表)。"""
    results: list[TestCase] = []
    failed: list[str] = []
    total = len(test_points)

    for i, point in enumerate(test_points, start=1):
        if on_progress:
            on_progress(i, total, point)
        try:
            case = generate_test_case(point, i, module_prefix, doc, config)
            results.append(case)
        except Exception as e:
            failed.append(point)
            print(f"\n警告: 测试点 [{i}] 生成失败，已跳过。原因：{e}")

    return results, failed


def _build_pass1_user_content(doc: ParsedDoc) -> str:
    parts = [f"## 文档概述\n{doc.overview}"]

    if doc.flowcharts:
        flowchart_text = "\n\n".join(
            f"```mermaid\n{fc}\n```" for fc in doc.flowcharts
        )
        parts.append(f"## 业务流程图\n{flowchart_text}")

    parts.append(f"## 功能设计\n{doc.feature_text}")
    parts.append(f"## 验收标准\n{doc.acceptance}")
    return "\n\n".join(parts)


def _format_id(prefix: str, index: int) -> str:
    width = max(3, len(str(index)))
    return f"{prefix}-{index:0{width}d}"
