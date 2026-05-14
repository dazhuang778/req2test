from pydantic import BaseModel, field_validator


class TestPointResult(BaseModel):
    module_name: str
    module_prefix: str
    test_points: list[str]

    @field_validator("module_prefix")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        if not v.isalpha() or not v.isupper():
            raise ValueError(f"module_prefix 必须为全大写英文字母，实际值：{v!r}")
        if not (3 <= len(v) <= 10):
            raise ValueError(f"module_prefix 长度须在 3-10 之间，实际长度：{len(v)}")
        return v

    @field_validator("test_points")
    @classmethod
    def validate_test_points(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("test_points 不能为空列表")
        return v


class TestCase(BaseModel):
    id: str
    title: str
    preconditions: str
    steps: str
    expected_result: str


class TestCaseBatch(BaseModel):
    test_cases: list[TestCase]
