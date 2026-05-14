import re
from dataclasses import dataclass, field


class ParseError(Exception):
    pass


@dataclass
class Section:
    title: str
    content: str


@dataclass
class ParsedDoc:
    overview: str
    flowcharts: list[str]
    feature_text: str
    acceptance: str
    raw_sections: list[Section] = field(default_factory=list)


_SECTION_PATTERN = re.compile(r"^(#{1,2}) (.+)$", re.MULTILINE)
_H1_PATTERN = re.compile(r"^# (.+)$", re.MULTILINE)
_MERMAID_PATTERN = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
_NUMBER_PREFIX = re.compile(r"^\d+[\.\d]*\s*")

_REQUIRED_SECTIONS = ("文档概述", "规划功能", "验收标准")


def _normalize_title(title: str) -> str:
    """去除数字编号前缀，如 '1. 文档概述' → '文档概述'"""
    return _NUMBER_PREFIX.sub("", title).strip()


def parse_document(text: str) -> ParsedDoc:
    sections = _split_sections(text)
    section_map = {_normalize_title(s.title): s.content for s in sections}

    for name in _REQUIRED_SECTIONS:
        if name not in section_map:
            raise ParseError(f"文档缺少必要章节：{name}")

    features_raw = section_map["规划功能"]
    flowcharts = [m.group(1).strip() for m in _MERMAID_PATTERN.finditer(features_raw)]
    feature_text = _MERMAID_PATTERN.sub("", features_raw).strip()

    return ParsedDoc(
        overview=section_map["文档概述"].strip(),
        flowcharts=flowcharts,
        feature_text=feature_text,
        acceptance=section_map["验收标准"].strip(),
        raw_sections=sections,
    )


def parse_sections(text: str) -> list[Section]:
    return _split_sections(text)


def _split_sections(text: str) -> list[Section]:
    """按顶层标题分割文档。优先按 h1 分割；若无 h1 则按 h2 分割。"""
    h1_matches = list(_H1_PATTERN.finditer(text))
    if h1_matches:
        matches = h1_matches
        title_group = 1
    else:
        matches = list(_SECTION_PATTERN.finditer(text))
        title_group = 2

    if not matches:
        return []

    sections: list[Section] = []
    for i, match in enumerate(matches):
        title = match.group(title_group).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append(Section(title=title, content=content))

    return sections
