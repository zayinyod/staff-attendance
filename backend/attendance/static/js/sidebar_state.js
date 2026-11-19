// サイドバーの固定状態の保存・復元と、表示方式の判定
// 描画前に固定状態を反映するため、head で同期的に読み込む。toggle.js は window.sidebarState を使う

(function () {
  const STORAGE_KEY = 'sidebar.pinned';
  // 狭い画面とホバーできない端末では、固定せずオーバーレイで開閉する [sidebar.css の 900px と揃える]
  const OVERLAY_QUERY = '(max-width: 899px), (hover: none)';

  // ストレージを使用できない環境 [プライベートモード等] では、固定していない状態として扱う
  function loadPinned() {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  }

  function savePinned(pinned) {
    try {
      localStorage.setItem(STORAGE_KEY, String(pinned));
    } catch {
      // 保存できない場合は画面遷移後に固定が解除されるのみで、操作は継続できる
    }
  }

  function isOverlayMode() {
    return window.matchMedia(OVERLAY_QUERY).matches;
  }

  window.sidebarState = { OVERLAY_QUERY, loadPinned, savePinned, isOverlayMode };

  if (!isOverlayMode() && loadPinned()) {
    document.documentElement.dataset.sidebar = 'pinned';
  }
})();
