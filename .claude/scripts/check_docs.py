#!/usr/bin/env python3
"""
仕様書 [README.md、docs/] と実装の整合性を検査する。

検査項目:
  tree      docs/architecture.md のディレクトリ構成に記載したパスが存在すること。
            子を列挙したディレクトリでは、Git 管理下の .py が全て記載されていること
  make      Makefile の "##" 付きターゲットと README.md のタスク表が一致すること
  env       settings.py が読み込む環境変数が .env.example と docs/architecture.md に記載されていること
  url       urls.py の name= が docs/features.md に記載されていること
  link      README.md と docs/ の相対リンクの参照先 [ファイル・見出し] が存在すること

Usage:
  check_docs.py [--only tree,make,env,url,link]

不一致がある場合は終了コード 1 を返す。
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = REPOSITORY_DIR / "docs"
README = REPOSITORY_DIR / "README.md"
ARCHITECTURE = DOCS_DIR / "architecture.md"
FEATURES = DOCS_DIR / "features.md"
MAKEFILE = REPOSITORY_DIR / "Makefile"
ENV_EXAMPLE = REPOSITORY_DIR / ".env.example"
DJANGO_DIR = REPOSITORY_DIR / "staff_attendance"
SETTINGS = DJANGO_DIR / "staff_attendance" / "settings.py"

TREE_HEADING = "## ディレクトリ構成"
# 一覧の網羅性を問わない .py
EXCLUDED_PYTHON_NAMES = {"__init__.py"}
EXCLUDED_PYTHON_DIRECTORIES = {"migrations", "tests"}


def read(path):
    return path.read_text(encoding="utf-8")


def remove_code_blocks(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPOSITORY_DIR, capture_output=True, text=True, check=True
    )
    return {REPOSITORY_DIR / line for line in result.stdout.splitlines()}


def parse_tree(text):
    """ディレクトリ構成のコードブロックを [パス, 子を列挙しているか] の一覧に変換する"""
    section = text.split(TREE_HEADING, 1)[1]
    block = re.search(r"```\n(.*?)```", section, flags=re.S).group(1)
    lines = block.splitlines()

    entries = []
    stack = []
    for line in lines[1:]:  # 1 行目はリポジトリのルート
        match = re.match(r"^((?:│   |    )*)(?:├── |└── )([^#\s]+)", line)
        if not match:
            continue
        depth = len(match.group(1)) // 4
        name = match.group(2)
        stack = stack[:depth] + [name.rstrip("/")]
        entries.append(Path(*stack))

    directories_with_children = {entry.parent for entry in entries if entry.parent != Path(".")}
    return entries, directories_with_children


def check_tree():
    findings = []
    entries, directories_with_children = parse_tree(read(ARCHITECTURE))
    for entry in entries:
        if not (REPOSITORY_DIR / entry).exists():
            findings.append(f"architecture.md に記載したパスが存在しない: {entry}")

    listed = {REPOSITORY_DIR / entry for entry in entries}
    for path in sorted(tracked_files()):
        if path.suffix != ".py" or path.name in EXCLUDED_PYTHON_NAMES:
            continue
        relative = path.relative_to(REPOSITORY_DIR)
        if EXCLUDED_PYTHON_DIRECTORIES & set(relative.parts):
            continue
        if relative.parent in directories_with_children and path not in listed:
            findings.append(f"architecture.md のディレクトリ構成に記載がない: {relative}")
    return findings


def check_make():
    targets = set(re.findall(r"^([a-zA-Z_-]+):.*?## ", read(MAKEFILE), flags=re.M))
    documented = set(re.findall(r"^\| `make ([a-zA-Z_-]+)[^`]*` \|", read(README), flags=re.M))
    findings = [f"README.md のタスク表に記載がない: make {name}" for name in sorted(targets - documented)]
    findings += [f"Makefile に存在しないタスクが README.md にある: make {name}" for name in sorted(documented - targets)]
    return findings


def check_env():
    variables = set(re.findall(r"""env(?:\.\w+)?\(\s*["'](\w+)["']""", read(SETTINGS)))
    example = set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]*)=", read(ENV_EXAMPLE), flags=re.M))
    architecture = read(ARCHITECTURE)

    findings = [f".env.example に記載がない環境変数: {name}" for name in sorted(variables - example)]
    findings += [f"settings.py が読み込まない環境変数が .env.example にある: {name}" for name in sorted(example - variables)]
    findings += [f"architecture.md に記載がない環境変数: {name}"
                 for name in sorted(variables) if f"`{name}`" not in architecture]
    return findings


def check_url():
    features = read(FEATURES)
    findings = []
    for path in sorted(DJANGO_DIR.rglob("urls.py")):
        for name in re.findall(r"""name=["'](\w+)["']""", read(path)):
            if f"`{name}`" not in features:
                findings.append(f"features.md に記載がない URL 名: {name} [{path.relative_to(REPOSITORY_DIR)}]")
    return findings


def heading_anchor(heading):
    """GitHub の見出しアンカーの規則に従って変換する"""
    anchor = heading.strip().lower()
    anchor = re.sub(r"[^\w\- ]", "", anchor)
    return anchor.replace(" ", "-")


def anchors_of(path):
    text = remove_code_blocks(read(path))
    return {heading_anchor(heading) for heading in re.findall(r"^#+\s+(.+)$", text, flags=re.M)}


def check_link():
    findings = []
    for document in [README, *sorted(DOCS_DIR.glob("*.md"))]:
        text = remove_code_blocks(read(document))
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if re.match(r"^[a-z]+:", target):
                continue
            file_part, _, anchor = target.partition("#")
            linked = (document.parent / file_part).resolve() if file_part else document
            label = f"{document.relative_to(REPOSITORY_DIR)} -> {target}"
            if not linked.exists():
                findings.append(f"リンク先が存在しない: {label}")
            elif anchor and linked.suffix == ".md" and anchor not in anchors_of(linked):
                findings.append(f"リンク先の見出しが存在しない: {label}")
    return findings


CHECKS = {
    "tree": check_tree,
    "make": check_make,
    "env": check_env,
    "url": check_url,
    "link": check_link,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="実行する検査をカンマ区切りで指定する")
    arguments = parser.parse_args()

    names = arguments.only.split(",") if arguments.only else list(CHECKS)
    unknown = set(names) - set(CHECKS)
    if unknown:
        parser.error(f"未定義の検査: {', '.join(sorted(unknown))}")

    total = 0
    for name in names:
        findings = CHECKS[name]()
        total += len(findings)
        print(f"[{name}] {'OK' if not findings else f'{len(findings)} 件'}")
        for finding in findings:
            print(f"  - {finding}")

    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
