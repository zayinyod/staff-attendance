#!/usr/bin/env python3
"""
darkmode-js の反転方式を前提に、配色の値を算出・検査する。

Dark Mode は画面全体を反転 [mix-blend-mode: difference] して表示するため、
Dark で表示される色は「指定した色の反転色」となる。背景も同様に反転する。

サブコマンド:
  pair      Light の色と Dark で見せたい色から、darkmode--activated に指定する値を算出する
  contrast  2 色のコントラスト比を表示する
  lint      CSS から反転で意図しない表示となる箇所を一覧にする
          [/* theme-color: allow */ を付けた行は対象外]
"""

import argparse
import re
import sys
from pathlib import Path

# 背景色は Light Mode の値。Dark Mode の背景はその反転色となる
BACKGROUNDS = {
    "page": ["#e1e1d7"],
    "table": ["#202122", "#27292d"],
}
MINIMUM_CONTRAST = 4.5
# 最大成分と最小成分の差がこれを超える色は有彩色とみなす [反転で色相が変わる]
CHROMATIC_THRESHOLD = 40

HEX_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
RGB_PATTERN = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
COLOR_PROPERTIES = ("color", "background", "background-color", "border", "border-color",
                    "outline", "box-shadow", "text-decoration-color", "fill", "stroke")
DARK_SELECTOR = "darkmode--activated"
# 反転後の色相の変化を許容する宣言に付ける目印 [同じ行のコメントに記す]
ALLOW_MARKER = "theme-color: allow"


def parse_color(value):
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        raise argparse.ArgumentTypeError(f"#rrggbb 形式で指定する: {value}")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def format_color(rgb):
    return "#" + "".join(f"{component:02x}" for component in rgb)


def invert(rgb):
    return tuple(255 - component for component in rgb)


def relative_luminance(rgb):
    def linearize(component):
        ratio = component / 255
        return ratio / 12.92 if ratio <= 0.03928 else ((ratio + 0.055) / 1.055) ** 2.4

    red, green, blue = (linearize(component) for component in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground, background):
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def is_chromatic(rgb):
    return max(rgb) - min(rgb) > CHROMATIC_THRESHOLD


def judge(ratio):
    return "OK" if ratio >= MINIMUM_CONTRAST else "NG"


def run_pair(arguments):
    light = arguments.light
    dark = arguments.dark
    backgrounds = arguments.background or [parse_color(color) for color in BACKGROUNDS[arguments.on]]
    override = invert(dark)
    failed = False

    print(f"Light に指定する値              : {format_color(light)}")
    print(f"darkmode--activated に指定する値: {format_color(override)}  /* 反転後 {format_color(dark)} */")
    print(f"上書きしない場合の Dark の表示  : {format_color(invert(light))}")
    print()
    print("| モード | 文字色 | 背景 | コントラスト比 | 判定 |")
    print("|---|---|---|---|---|")
    for background in backgrounds:
        for mode, foreground, shown_background in (
            ("Light", light, background),
            ("Dark", dark, invert(background)),
        ):
            ratio = contrast_ratio(foreground, shown_background)
            failed |= ratio < MINIMUM_CONTRAST
            print(f"| {mode} | {format_color(foreground)} | {format_color(shown_background)} "
                  f"| {ratio:.2f}:1 | {judge(ratio)} |")
    return 1 if failed else 0


def run_contrast(arguments):
    ratio = contrast_ratio(arguments.foreground, arguments.background)
    print(f"{format_color(arguments.foreground)} / {format_color(arguments.background)}: "
          f"{ratio:.2f}:1 {judge(ratio)}")
    return 0 if ratio >= MINIMUM_CONTRAST else 1


def extract_colors(value):
    colors = [parse_color(match) for match in HEX_PATTERN.findall(value)]
    colors += [tuple(int(component) for component in match) for match in RGB_PATTERN.findall(value)]
    return colors


def iterate_rules(text):
    """コメントを除去し、最内側の宣言ブロックを [selector, 行番号, 宣言] の形で返す"""
    text = re.sub(r"/\*.*?\*/", lambda match: re.sub(r"[^\n]", " ", match.group()), text, flags=re.S)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        selector = " ".join(match.group(1).split())
        body_start = match.start(2)
        for declaration in re.finditer(r"([-\w]+)\s*:\s*([^;]+)", match.group(2)):
            line_number = text.count("\n", 0, body_start + declaration.start()) + 1
            yield selector, line_number, declaration.group(1).lower(), declaration.group(2).strip()


def run_lint(arguments):
    paths = []
    for path in arguments.paths:
        path = Path(path)
        paths += sorted(path.rglob("*.css")) if path.is_dir() else [path]

    declarations = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for selector, line_number, name, value in iterate_rules(text):
            if ALLOW_MARKER in lines[line_number - 1]:
                continue
            declarations.append((path, selector, line_number, name, value))

    # Dark で上書きされている変数 [全ファイル共通]
    overridden_variables = {
        name for _, selector, _, name, _ in declarations
        if DARK_SELECTOR in selector and name.startswith("--")
    }

    findings = []
    for path, selector, line_number, name, value in declarations:
        location = f"{path}:{line_number}"
        if DARK_SELECTOR in selector:
            continue
        if name == "isolation" and value == "isolate":
            findings.append((location, selector, "isolation: isolate により反転の対象外となり、Light / Dark で同色となる"))
            continue
        chromatic_colors = [color for color in extract_colors(value) if is_chromatic(color)]
        if not chromatic_colors:
            continue
        shown = ", ".join(format_color(color) for color in chromatic_colors)
        if name.startswith("--"):
            if name not in overridden_variables:
                findings.append((location, selector,
                                 f"{name}: {shown} は Dark の上書きがなく、反転後は {format_color(invert(chromatic_colors[0]))} となる"))
        elif name in COLOR_PROPERTIES or name.endswith("color"):
            findings.append((location, selector,
                             f"{name}: {shown} を直接指定している。変数化して Dark の値を上書きするか確認する"))

    for location, selector, message in findings:
        print(f"{location}  [{selector}]  {message}")
    print(f"\n{len(findings)} 件 [既存分を含む。終了コードは常に 0]")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    pair = subparsers.add_parser("pair", help="darkmode--activated に指定する値を算出する")
    pair.add_argument("light", type=parse_color, help="Light で表示する色")
    pair.add_argument("dark", type=parse_color, help="Dark で表示したい色 [反転後の見え方]")
    pair.add_argument("--on", choices=BACKGROUNDS, default="page", help="背景の種類 [既定: page]")
    pair.add_argument("--background", type=parse_color, action="append",
                      help="Light の背景色を直接指定する [複数可。--on より優先]")
    pair.set_defaults(handler=run_pair)

    contrast = subparsers.add_parser("contrast", help="2 色のコントラスト比を表示する")
    contrast.add_argument("foreground", type=parse_color)
    contrast.add_argument("background", type=parse_color)
    contrast.set_defaults(handler=run_contrast)

    lint = subparsers.add_parser("lint", help="CSS の配色を検査する")
    lint.add_argument("paths", nargs="+", help="CSS ファイルまたはディレクトリ")
    lint.set_defaults(handler=run_lint)
    return parser


def main():
    arguments = build_parser().parse_args()
    sys.exit(arguments.handler(arguments))


if __name__ == "__main__":
    main()
