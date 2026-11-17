// ページに埋め込まれた割り当てを読み込み、ショートカットを有効にする

import { startKeymap } from './keymap.js';

const source = document.getElementById('shortcut-bindings');
if (source) {
  startKeymap(JSON.parse(source.textContent));
}
