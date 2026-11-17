// サイドバーの開閉

import { registerAction } from './shortcuts/actions.js';

const nav = document.querySelector('nav.sidebar');
const toggleButton = document.querySelector('.toggle-btn');
const mask = document.querySelector('#mask');

function isSidebarOpen() {
  return nav.classList.contains('open');
}

function toggleSidebar() {
  nav.classList.toggle('open');
}

// 開いていない場合は何もせず false を返し、Esc の既定動作を妨げない
function closeSidebar() {
  if (!isSidebarOpen()) {
    return false;
  }
  nav.classList.remove('open');
}

if (nav) {
  toggleButton.addEventListener('click', toggleSidebar);
  mask.addEventListener('click', closeSidebar);

  registerAction('sidebar.toggle', toggleSidebar);
  registerAction('sidebar.close', closeSidebar);
}
