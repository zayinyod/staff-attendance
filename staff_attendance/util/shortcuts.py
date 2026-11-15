"""
ショートカットキーの割り当てを提供する。

割り当てはアクション ID とキー表記のリストの対応で表す。
キー表記は修飾キーと主キーを "+" で連結する [e.g. "Alt+O", "Ctrl+Shift+K", "Escape"]
アクションの処理は static/js/shortcuts/actions.js に登録する。
"""

from copy import deepcopy

DEFAULT_SHORTCUTS = {
    "sidebar.toggle": ["Alt+O"],
    "sidebar.close": ["Escape"],
}


def resolve_shortcuts(user) -> dict:
    """
    ユーザーに適用する割り当てを返す。
    ユーザー単位のカスタマイズを導入する際は、ここで設定値を既定値に上書きする。
    """
    return deepcopy(DEFAULT_SHORTCUTS)


def shortcut_bindings(request) -> dict:
    """
    テンプレートに割り当てを渡すコンテキストプロセッサ
    """
    return {"shortcut_bindings": resolve_shortcuts(request.user)}
