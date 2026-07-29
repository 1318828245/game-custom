from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLE_DIR = ROOT / "角色"
HANDOFF_DIR = ROLE_DIR / "交接区"
ARCHIVE_DIR = ROLE_DIR / "交接归档"
SUMMARY_FILE = ROLE_DIR / "自动汇总.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def list_handoffs() -> list[Path]:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        [path for path in HANDOFF_DIR.glob("*.md") if path.name != "README.md"],
        key=lambda path: (path.stat().st_mtime, path.name),
    )


def build_summary() -> str:
    handoffs = list_handoffs()
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
        lines.append(f"- {path.relative_to(ROOT).as_posix()}")

    for path in handoffs:
        rel = path.relative_to(ROOT).as_posix()
        lines.extend(["", "---", "", f"## {rel}", ""])
        lines.append(read_text(path).strip())
        lines.append("")

    return "\n".join(lines)


def init_dirs() -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    readme = HANDOFF_DIR / "README.md"
    if not readme.exists():
        write_text(
            readme,
            """# 交接区

每个角色窗口完成一轮工作后，把交接内容写成一个新的 Markdown 文件放到本目录。

命名建议：

- `2026-07-29_游戏策划_MVP设计.md`
- `2026-07-29_程序开发_技术评估.md`
- `2026-07-29_美术设计_资源规划.md`
- `2026-07-29_音效音乐_音频规划.md`

角色窗口只新增交接文件，不直接修改其他角色的交接文件。
""",
        )


def archive_handoffs() -> int:
    handoffs = list_handoffs()
    if not handoffs:
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = ARCHIVE_DIR / stamp
    target_dir.mkdir(parents=True, exist_ok=True)

    for path in handoffs:
        path.replace(target_dir / path.name)

    return len(handoffs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Role collaboration helper")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="create collaboration folders")
    subparsers.add_parser("summary", help="build 角色/自动汇总.md from handoff files")
    subparsers.add_parser("archive", help="move current handoff files into 角色/交接归档")
    args = parser.parse_args()

    if args.command == "init":
        init_dirs()
        print(f"Initialized: {HANDOFF_DIR}")
    elif args.command == "summary":
        init_dirs()
        write_text(SUMMARY_FILE, build_summary())
        print(f"Wrote: {SUMMARY_FILE}")
    elif args.command == "archive":
        init_dirs()
        count = archive_handoffs()
        print(f"Archived handoff files: {count}")


if __name__ == "__main__":
    main()
