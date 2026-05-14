import io
import sys
from pathlib import Path

import click

# Windows 控制台强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from openai import APIStatusError

from .config import load_config
from .exporter import export_to_excel
from .generator import generate_all_cases, generate_test_points, refine_test_points
from .parser import ParseError, parse_document

_SEP = "━" * 40


def _print_test_points(result) -> None:
    click.echo(f"\n{_SEP}")
    click.echo(f"模块: {result.module_name} [{result.module_prefix}]")
    click.echo(_SEP)
    for i, point in enumerate(result.test_points, 1):
        click.echo(f"  {i}. {point}")
    click.echo(f"\n共 {len(result.test_points)} 个测试点")
    click.echo(_SEP)


def _confirm_loop(result, messages, config):
    """多轮对话确认交互。返回最终确认的 TestPointResult，或 None 表示取消。"""
    while True:
        _print_test_points(result)
        user_input = click.prompt(
            "[y] 确认并生成测试用例  [n] 取消  [或输入说明与 AI 对话调整]",
            default="y",
            show_default=False,
        ).strip()

        if user_input.lower() in ("y", ""):
            return result
        if user_input.lower() == "n":
            click.echo("已取消。")
            return None

        click.echo("正在根据您的说明调整测试点...")
        try:
            result, messages = refine_test_points(user_input, messages, config)
        except Exception as e:
            click.echo(f"调整失败：{e}", err=True)


def _process_file(
    input_path: Path,
    output_path: Path,
    config,
    context: str,
) -> bool:
    """处理单个 MD 文件。返回是否成功。"""
    click.echo(f"\n正在解析文档...")
    try:
        text = input_path.read_text(encoding="utf-8")
        doc = parse_document(text)
    except ParseError as e:
        click.echo(f"Error: 文档解析失败：{e}", err=True)
        return False
    click.echo("✓ 文档解析完成")

    click.echo("正在生成测试点...")
    try:
        result, messages = generate_test_points(doc, config, context=context)
    except APIStatusError as e:
        _handle_api_error(e)
        return False
    except Exception as e:
        click.echo(f"Error: 生成测试点失败：{e}", err=True)
        return False
    click.echo("✓ 测试点生成完成")

    confirmed = _confirm_loop(result, messages, config)
    if confirmed is None:
        return False

    if output_path.exists():
        click.echo(f"注意: {output_path} 已存在，将被覆盖。")

    click.echo(f"\n正在生成测试用例（共 {len(confirmed.test_points)} 个测试点）...")

    def on_progress(current, total, point):
        click.echo(f"  [{current}/{total}] 生成测试用例: {point}")

    try:
        cases, failed = generate_all_cases(
            confirmed.test_points,
            confirmed.module_prefix,
            doc,
            config,
            on_progress=on_progress,
        )
    except APIStatusError as e:
        _handle_api_error(e)
        return False

    if not cases:
        click.echo("Error: 所有测试点均生成失败，未导出 Excel。", err=True)
        return False

    if failed:
        click.echo(f"\n警告: {len(failed)} 个测试点生成失败，已跳过：")
        for p in failed:
            click.echo(f"  - {p}")

    export_to_excel(cases, output_path)
    click.echo(f"\n✓ 导出完成: {output_path}  ({len(cases)} 条用例)")

    points_path = output_path.with_name(output_path.stem + "_points.txt")
    _save_test_points(confirmed, points_path)
    click.echo(f"✓ 测试点已保存: {points_path}  ({len(confirmed.test_points)} 个测试点)")
    return True


def _save_test_points(result, path: Path) -> None:
    lines = [f"模块: {result.module_name} [{result.module_prefix}]", ""]
    for i, point in enumerate(result.test_points, 1):
        lines.append(f"{i}. {point}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _handle_api_error(e: APIStatusError) -> None:
    status = e.status_code
    if status == 401:
        click.echo(
            "Error: API 认证失败 (401)，请检查 config.yaml 中的 api_key。",
            err=True,
        )
    elif status == 429:
        click.echo(
            "Error: 请求频率超限 (429)，请稍后重试或降低并发。",
            err=True,
        )
    else:
        click.echo(f"Error: LLM API 请求失败 ({status})：{e.message}", err=True)
    sys.exit(1)


@click.command()
@click.option("-i", "--input", "input_path", required=True, help="输入的 MD 文件或目录路径")
@click.option("-o", "--output", "output_path", required=True, help="输出的 Excel 文件路径（文件模式）或目录（目录模式）")
@click.option("--context", default="", help="额外上下文说明，注入 LLM prompt 辅助生成（如：重点关注安全场景）")
def cli(input_path: str, output_path: str, context: str) -> None:
    """testgen — 从 MD 需求文档自动生成测试用例 Excel"""
    ipath = Path(input_path)
    opath = Path(output_path)

    if not ipath.exists():
        click.echo(f"Error: 路径不存在: {ipath}", err=True)
        sys.exit(1)

    config = load_config()

    if ipath.is_file():
        _run_single(ipath, opath, config, context)
    else:
        _run_directory(ipath, opath, config, context)


def _run_single(ipath: Path, opath: Path, config, context: str) -> None:
    success = _process_file(ipath, opath, config, context)
    if not success:
        sys.exit(1)


def _run_directory(ipath: Path, opath: Path, config, context: str) -> None:
    md_files = sorted(ipath.glob("*.md"))
    if not md_files:
        click.echo(f"Error: 目录中未找到 .md 文件: {ipath}", err=True)
        sys.exit(1)

    opath.mkdir(parents=True, exist_ok=True)
    total = len(md_files)
    click.echo(f"发现 {total} 个 MD 文件，开始处理...")

    succeeded, failed_files = [], []
    for idx, md_file in enumerate(md_files, 1):
        click.echo(f"\n{'═' * 50}")
        click.echo(f"[{idx}/{total}] 处理: {md_file.name}")
        click.echo(f"{'═' * 50}")

        out_file = opath / f"{md_file.stem}_cases.xlsx"
        ok = _process_file(md_file, out_file, config, context)
        if ok:
            succeeded.append(md_file.name)
        else:
            failed_files.append(md_file.name)

    click.echo(f"\n{'═' * 50}")
    click.echo(f"处理完成：成功 {len(succeeded)}/{total}")
    if failed_files:
        click.echo(f"失败 {len(failed_files)}/{total}:")
        for f in failed_files:
            click.echo(f"  - {f}")


if __name__ == "__main__":
    cli()
