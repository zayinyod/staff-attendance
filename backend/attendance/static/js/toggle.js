// サイドバーの表示状態の管理
// 状態は html 要素の data-sidebar で表す
//   closed: 非表示
//   peek:   開閉ボタンへのホバー中の一時表示
//   pinned: 固定表示 [本文を右に寄せる。状態を保存する]
//   open:   オーバーレイ表示 [狭い画面・ホバーできない端末。幕を表示する]

import { registerAction } from './shortcuts/actions.js';

// ボタンとサイドバーの間をカーソルが往復する際に閉じないよう、閉じるまでに猶予を置く
const PEEK_CLOSE_DELAY_MS = 300;

const root = document.documentElement;
const nav = document.getElementById('sidebar');
const toggleButton = document.getElementById('sidebar-toggle');
const mask = document.getElementById('sidebar-mask');
const sidebarState = window.sidebarState;

let closeTimer = null;

function getState() {
  return root.dataset.sidebar ?? 'closed';
}

function setState(state) {
  root.dataset.sidebar = state;
  toggleButton.setAttribute('aria-expanded', String(state !== 'closed'));
}

function cancelScheduledClose() {
  clearTimeout(closeTimer);
  closeTimer = null;
}

function peekSidebar() {
  cancelScheduledClose();
  if (getState() === 'closed' && !sidebarState.isOverlayMode()) {
    setState('peek');
  }
}

function scheduleClose() {
  if (getState() !== 'peek') {
    return;
  }
  cancelScheduledClose();
  closeTimer = setTimeout(() => {
    if (getState() === 'peek') {
      setState('closed');
    }
  }, PEEK_CLOSE_DELAY_MS);
}

function toggleSidebar() {
  cancelScheduledClose();
  if (sidebarState.isOverlayMode()) {
    setState(getState() === 'open' ? 'closed' : 'open');
    return;
  }
  const pinned = getState() !== 'pinned';
  setState(pinned ? 'pinned' : 'closed');
  sidebarState.savePinned(pinned);
}

// 一時表示とオーバーレイのみ閉じる。固定中・閉じている場合は false を返し、Esc の既定動作を妨げない
function closeSidebar() {
  const state = getState();
  if (state !== 'peek' && state !== 'open') {
    return false;
  }
  cancelScheduledClose();
  setState('closed');
}

// 画面幅の変化で表示方式が切り替わった場合は、固定状態を保存値から復元する
function applyLayoutMode() {
  cancelScheduledClose();
  const pinned = !sidebarState.isOverlayMode() && sidebarState.loadPinned();
  setState(pinned ? 'pinned' : 'closed');
}

if (nav && toggleButton && mask && sidebarState) {
  toggleButton.addEventListener('mouseenter', peekSidebar);
  toggleButton.addEventListener('mouseleave', scheduleClose);
  toggleButton.addEventListener('click', toggleSidebar);
  nav.addEventListener('mouseenter', cancelScheduledClose);
  nav.addEventListener('mouseleave', scheduleClose);
  mask.addEventListener('click', closeSidebar);
  window.matchMedia(sidebarState.OVERLAY_QUERY).addEventListener('change', applyLayoutMode);

  // 復元済みの状態を aria-expanded に反映する
  setState(getState());

  registerAction('sidebar.toggle', toggleSidebar);
  registerAction('sidebar.close', closeSidebar);
}
