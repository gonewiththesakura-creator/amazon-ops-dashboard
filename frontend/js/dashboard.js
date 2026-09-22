// Dashboard (Overview) View Controller
const DashboardView = {
  async init() {
    await this.loadBriefing();
    await this.loadCoreSkusTable();
  },

  async loadBriefing() {
    const res = await API.getBriefing();
    if (!res || res.status !== "ok" || !res.data) return;

    const briefing = res.data;

    // 1. Render Top AI Briefing 3 Bullets
    const bulletsContainer = document.getElementById("briefingBullets");
    if (bulletsContainer && briefing.bullets) {
      bulletsContainer.innerHTML = briefing.bullets.map(b => `
        <div class="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
          <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
            ${b.id}
          </span>
          <div class="text-xs">
            <span class="font-bold text-slate-900">${b.highlight}：</span>
            <span class="text-slate-700">${b.detail}</span>
            <span class="ml-2 font-mono text-[10px] text-slate-400 bg-white px-1.5 py-0.5 rounded border border-slate-200">证据: ${b.evidence}</span>
          </div>
        </div>
      `).join("");
    }

    // 2. Render Left Big Card (Market Overview)
    const m = briefing.marketSummary || {};
    document.getElementById("cardMarketGrowth").textContent = m.growth30d || "--";
    document.getElementById("cardMarketCapacity").textContent = m.capacity || "--";
    document.getElementById("cardMarketMonopoly").textContent = m.monopolyLevel || "--";
    document.getElementById("cardMarketRisk").textContent = m.primaryRisk || "--";

    // 3. Render Right Big Card (4 SKU Performance)
    const s = briefing.skusSummary || {};
    document.getElementById("countOutperforming").textContent = s.outperforming || 0;
    document.getElementById("countPar").textContent = s.par || 0;
    document.getElementById("countUnderperforming").textContent = s.underperforming || 0;
    document.getElementById("countPending").textContent = s.pending || 0;
    document.getElementById("cardSkuDiagnosis").textContent = s.diagnosis || "--";
  },

  async loadCoreSkusTable() {
    const res = await API.getCoreProductsComparison();
    if (!res || res.status !== "ok" || !res.data) return;

    const tbody = document.getElementById("homeSkuTableBody");
    if (!tbody) return;

    const skus = res.data.skus || [];
    tbody.innerHTML = skus.map(s => {
      let badgeClass = "badge-gray";
      let statusIcon = "•";
      if (s.comparisonStatus === "outperforming") {
        badgeClass = "badge-green";
        statusIcon = "↑ 跑赢大盘";
      } else if (s.comparisonStatus === "underperforming") {
        badgeClass = "badge-rose";
        statusIcon = "↓ 跑输大盘";
      } else if (s.comparisonStatus === "par") {
        badgeClass = "badge-blue";
        statusIcon = "→ 持平大盘";
      } else {
        badgeClass = "badge-amber";
        statusIcon = "待配置";
      }

      const priceStr = s.price ? `$${s.price}` : "<span class='text-slate-400'>--</span>";
      const bsrStr = s.bsr ? `#${Number(s.bsr).toLocaleString()}` : "<span class='text-slate-400'>--</span>";

      return `
        <tr class="hover:bg-slate-50 transition border-b border-slate-100 text-xs">
          <td class="py-3 px-4">
            <div class="font-bold text-slate-900">${s.name}</div>
            <div class="font-mono text-[11px] text-slate-400">${s.sku} | ${s.asin}</div>
          </td>
          <td class="py-3 px-4 font-mono font-medium">${priceStr}</td>
          <td class="py-3 px-4 font-mono">${bsrStr}</td>
          <td class="py-3 px-4">
            <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${badgeClass}">
              ${statusIcon}
            </span>
          </td>
          <td class="py-3 px-4 font-mono text-slate-600">${s.trend30d}</td>
          <td class="py-3 px-4 text-slate-600 font-medium">${s.aiState}</td>
          <td class="py-3 px-4 text-right">
            ${s.asin !== 'PENDING_SKU_4' ? `
              <button onclick="App.navigateTo('products', '${s.asin}')" class="text-blue-600 hover:text-blue-800 font-medium text-xs">
                进入战情室 ➔
              </button>
            ` : `
              <span class="text-slate-400 text-xs">等待配置</span>
            `}
          </td>
        </tr>
      `;
    }).join("");
  }
};
