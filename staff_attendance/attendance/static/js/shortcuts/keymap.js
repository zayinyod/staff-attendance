// キー入力を割り当てと照合し、対応するアクションを実行する
// 割り当ては { アクション ID: [キー表記, ...] } の形式で受け取る [util/shortcuts.py]

import { runAction } from './actions.js';

const MODIFIER_ORDER = ['Ctrl', 'Alt', 'Shift', 'Meta'];
const MODIFIER_ALIASES = { control: 'Ctrl', ctrl: 'Ctrl', alt: 'Alt', option: 'Alt', shift: 'Shift', meta: 'Meta', cmd: 'Meta' };

// 入力中は誤動作を避けるため、ここに含まれるキーのみ受け付ける
const KEYS_ALLOWED_WHILE_TYPING = new Set(['Escape']);

function normalizeMainKey(key) {
  return key.length === 1 ? key.toUpperCase() : key;
}

function formatKey(modifiers, mainKey) {
  const ordered = MODIFIER_ORDER.filter((modifier) => modifiers.has(modifier));
  return [...ordered, normalizeMainKey(mainKey)].join('+');
}

// "alt+o" や "Shift+Ctrl+k" などの表記を "Alt+O" "Ctrl+Shift+K" の形に揃える
export function normalizeBinding(binding) {
  const parts = binding.split('+').map((part) => part.trim()).filter(Boolean);
  const mainKey = parts.pop();
  const modifiers = new Set(parts.map((part) => MODIFIER_ALIASES[part.toLowerCase()] ?? part));
  return formatKey(modifiers, mainKey);
}

// Alt などとの組み合わせで event.key が別の文字になる環境 [e.g. macOS] があるため、
// 英数字は物理キーの event.code から主キーを求める
function mainKeyFromEvent(event) {
  const match = /^(?:Key|Digit)(.)$/.exec(event.code);
  return match ? match[1] : event.key;
}

export function eventToBinding(event) {
  const modifiers = new Set();
  if (event.ctrlKey) modifiers.add('Ctrl');
  if (event.altKey) modifiers.add('Alt');
  if (event.shiftKey) modifiers.add('Shift');
  if (event.metaKey) modifiers.add('Meta');
  return formatKey(modifiers, mainKeyFromEvent(event));
}

export function buildKeymap(bindingsByAction) {
  const keymap = new Map();
  for (const [actionId, bindings] of Object.entries(bindingsByAction)) {
    for (const binding of bindings) {
      const key = normalizeBinding(binding);
      if (keymap.has(key)) {
        console.warn(`Shortcut "${key}" is assigned to both "${keymap.get(key)}" and "${actionId}".`);
        continue;
      }
      keymap.set(key, actionId);
    }
  }
  return keymap;
}

function isTyping(target) {
  return target instanceof HTMLElement
    && (target.matches('input, textarea, select') || target.isContentEditable);
}

export function startKeymap(bindingsByAction) {
  const keymap = buildKeymap(bindingsByAction);

  document.addEventListener('keydown', (event) => {
    if (event.repeat || event.isComposing) {
      return;
    }

    const binding = eventToBinding(event);
    const actionId = keymap.get(binding);
    if (!actionId) {
      return;
    }
    if (isTyping(event.target) && !KEYS_ALLOWED_WHILE_TYPING.has(binding)) {
      return;
    }

    if (runAction(actionId)) {
      event.preventDefault();
    }
  });
}
