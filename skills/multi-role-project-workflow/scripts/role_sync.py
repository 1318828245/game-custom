from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def list_handoffs(handoff_dir: Path) -> list[Path]:
    handoff_dir.mkdir(parents=True, exist_ok=True)
    return sorted(
        [path for path in handoff_dir.glob("*.md") if path.name.upper() != "README.md"],
        key=lambda path: (path.stat().st_mtime, path.name),
    )


def build_summary(root: Path, role_dir: Path, handoff_dir: Path) -> str:
    handoffs = list_handoffs(handoff_dir)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# 自动汇总",
        "",
        f"生成时间：{now}",
        "",
        "本文件由 `python tools/role_sync.py summary` 生成，用于主控窗口快速读取各角色交接内容。",
        "",
    ]

    if not handoffs:
        lines.extend(["## 当前没有交接文件", ""])
        return "\n".join(lines)

    lines.extend(["## 交接文件列表", ""])
    for path in handoffs:
        lines.append(f"- {path.relative_to(root).as_posix()}")

    for path in handoffs:
        rel = path.relative_to(root).as_posix()
        lines.extend(["", "---", "", f"## {rel}", ""])
        lines.append(read_text(path).strip())
        lines.append("")

    return "\n".join(lines)


def init_dirs(handoff_dir: Path, archive_dir: Path) -> None:
    handoff_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    readme = handoff_dir / "README.md"
    if not readme.exists():
        write_text(
            readme,
            """# 交接区

每个角色窗口完成一轮工作后，把交接内容写成一个新的 Markdown 文件放到本目录。

命名建议：

- `YYYY-MM-DD_角色名_任务名.md`

角色窗口只新增交接文件，不直接修改其他角色的交接文件。
""",
        )


def archive_handoffs(handoff_dir: Path, archive_dir: Path) -> int:
    handoffs = list_handoffs(handoff_dir)
    if not handoffs:
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = archive_dir / stamp
    target_dir.mkdir(parents=True, exist_ok=True)

    for path in handoffs:
        path.replace(target_dir / path.name)

    return len(handoffs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Role collaboration helper")
    parser.add_argument("--role-dir", default="角色", help="role collaboration directory")
    parser.add_argument("--handoff-dir", default=None, help="active handoff directory")
    parser.add_argument("--archive-dir", default=None, help="handoff archive directory")
    parser.add_argument("--summary-file", default=None, help="generated summary file")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="create collaboration folders")
    subparsers.add_parser("summary", help="build summary from handoff files")
    subparsers.add_parser("archive", help="move current handoff files into archive")
    args = parser.parse_args()

    root = Path.cwd()
    role_dir = root / args.role_dir
    handoff_dir = root / args.handoff_dir if args.handoff_dir else role_dir / "交接区"
    archive_dir = root / args.archive_dir if args.archive_dir else role_dir / "交接归档"
    summary_file = root / args.summary_file if args.summary_file else role_dir / "自动汇总.md"

    if args.command == "init":
        init_dirs(handoff_dir, archive_dir)
        print(f"Initialized: {handoff_dir}")
    elif args.command == "summary":
        init_dirs(handoff_dir, archive_dir)
        write_text(summary_file, build_summary(root, role_dir, handoff_dir))
        print(f"Wrote: {summary_file}")
    elif args.command == "archive":
        init_dirs(handoff_dir, archive_dir)
        count = archive_handoffs(handoff_dir, archive_dir)
        print(f"Archived handoff files: {count}")


if __name__ == "__main__":
    main()
