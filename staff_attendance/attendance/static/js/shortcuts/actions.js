// ショートカットから呼び出すアクションの登録先
// 画面側のモジュールがアクション ID と処理を登録し、keymap.js が ID で呼び出す。

const handlers = new Map();

export function registerAction(actionId, handler) {
  if (handlers.has(actionId)) {
    console.warn(`Shortcut action "${actionId}" is already registered. Overwriting.`);
  }
  handlers.set(actionId, handler);
}

// 処理を実行した場合は true を返す。未登録、または処理が false を返した場合は false を返す
export function runAction(actionId) {
  const handler = handlers.get(actionId);
  if (!handler) {
    return false;
  }
  return handler() !== false;
}
