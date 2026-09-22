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

    // 1. Render Top AI Briefing 4 Facts
    const bulletsContainer = document.getElementById("briefingBullets");
    if (bulletsContainer && briefing.bullets) {
      bulletsContainer.innerHTML = briefing.bullets.map(b => `
        <div class="flex flex-col justify-between p-3.5 rounded-lg bg-slate-50 border border-slate-200">
          <div>
            <div class="flex items-center gap-2 mb-1.5">
              <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                ${b.id}
              </span>
              <span class="text-xs font-bold text-slate-800">${b.title || `事实 ${b.id}`}</span>
            </div>
            <div class="text-xs font-semibold text-slate-900 leading-snug">${b.highlight}</div>
            <div class="text-[11px] text-slate-600 mt-1 leading-relaxed">${b.detail}</div>
          </div>
          <div class="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between">
            <span class="text-[10px] text-slate-400 font-mono">证据: ${b.evidence}</span>
          </div>
        </div>
      `).join("");
    }

    // 1b. Render 4 Direct Action Buttons
    const actionsContainer = document.getElementById("briefingActions");
    if (actionsContainer && briefing.actions) {
      actionsContainer.innerHTML = briefing.actions.map(a => `
        <button onclick="App.navigateTo('${a.target}')" class="flex items-center gap-2.5 p-2.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 transition text-left group">
          <span class="text-xl group-hover:scale-110 transition-transform">${a.icon}</span>
          <div>
            <div class="text-xs font-bold text-slate-800 group-hover:text-blue-600">${a.label}</div>
            <div class="text-[10px] text-slate-400">${a.desc}</div>
          </div>
        </button>
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
