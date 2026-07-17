// 共用 App Header：股票估價工具／財金早報兩個分頁用同一份程式碼產生
// header + 分頁列，統一配色與排版，之後要調視覺只改這一處。
// v8.17起兩頁合併成同一個index.html的SPA，分頁改成JS切換（見index.html的
// switchTab()），不再整頁跳轉；index_v6_ai.html保留成redirect stub供舊書籤使用。
function renderAppHeader({ containerSelector, activeTab, icon, title, version, subtitle, showProgress }) {
  const tabs = [
    { key: 'valuation', icon: '📊', label: '股票估價工具' },
    { key: 'report', icon: '🤖', label: '財金早報' },
  ];

  const tabsHtml = tabs.map(t => {
    const active = t.key === activeTab;
    const hoverAttrs = active ? '' : ` onmouseover="this.style.color='var(--text)';this.style.background='#fff'" onmouseout="this.style.color='var(--muted)';this.style.background='#f9fafb'"`;
    return `<a href="#${t.key}" data-tab-link="${t.key}" onclick="event.preventDefault();switchTab('${t.key}')" style="flex:1;padding:14px 20px;text-decoration:none;color:${active ? 'var(--text)' : 'var(--muted)'};font-weight:600;border-bottom:3px solid ${active ? 'var(--accent)' : 'transparent'};background:${active ? '#fff' : '#f9fafb'};text-align:center;display:flex;align-items:center;justify-content:center;gap:8px;transition:all .3s;"${hoverAttrs}>${t.icon} ${t.label}</a>`;
  }).join('');

  const progressHtml = showProgress ? `
    <div style="margin-top:12px;font-size:0.85rem;color:rgba(255,255,255,0.8);display:flex;gap:1rem;flex-wrap:wrap;align-items:center;">
      <span>📊 財務數據更新進度 (台股全市場：上市+上櫃+興櫃)：</span>
      <span style="background:rgba(255,255,255,0.15);padding:4px 10px;border-radius:8px;font-weight:600;">
        <span id="update-count">0</span>/<span id="total-count">2,303</span>
        (<span id="update-pct">0.2</span>%)
      </span>
      <span style="display:inline-block;width:80px;height:6px;background:rgba(255,255,255,0.2);border-radius:3px;overflow:hidden;">
        <div id="progress-bar" style="height:100%;width:31%;background:rgba(255,255,255,0.9);transition:width 0.3s ease;"></div>
      </span>
    </div>` : '';

  const container = document.querySelector(containerSelector);
  if (!container) return;
  container.innerHTML = `
<div class="header">
  <div class="header-content">
    <h1>${icon} ${title} <span class="vsub">v${version}</span></h1>
    <p class="sub">${subtitle}</p>
    ${progressHtml}
  </div>
</div>
<div style="display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:20px;">
  ${tabsHtml}
</div>`;
}
