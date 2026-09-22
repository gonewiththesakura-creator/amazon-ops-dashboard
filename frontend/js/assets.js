// Local Data Warehouse Assets Module
const DataAssets = {
  async init() {
    this.bindEvents();
    await this.loadAssetMetrics();
    // Default search with empty or recent
    await this.performSearch("B0");
  },

  bindEvents() {
    const searchBtn = document.getElementById("btnSearchAssets");
    const searchInput = document.getElementById("inputSearchAssets");
    const filterSelect = document.getElementById("selectAssetType");

    if (searchBtn) {
      searchBtn.onclick = () => {
        const q = searchInput ? searchInput.value.trim() : "";
        const t = filterSelect ? filterSelect.value : "";
        this.performSearch(q, t);
      };
    }

    if (searchInput) {
      searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          const q = searchInput.value.trim();
          const t = filterSelect ? filterSelect.value : "";
          this.performSearch(q, t);
        }
      });
    }

    // Modal close button
    const closeBtn = document.getElementById("closeRawModalBtn");
    if (closeBtn) {
      closeBtn.onclick = () => this.closeRawModal();
    }
  },

  async loadAssetMetrics() {
    const res = await API.getAssetStats();
    if (res.status === "ok" && res.data) {
      const d = res.data;
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = (typeof val === "number") ? val.toLocaleString() : (val || "--");
      };

      setVal("metricAsinCount", d.asinCount);
      setVal("metricPricePoints", d.pricePointsCount);
      setVal("metricBsrPoints", d.bsrPointsCount);
      setVal("metricSalesPoints", d.salesPointsCount);
      setVal("metricKeywordCount", d.keywordCount);
      setVal("metricMarketSnapshots", d.marketSnapshotsCount);
      setVal("metricTop100Records", d.top100RecordsCount);
      setVal("metricRawResponses", d.rawResponsesCount);
      setVal("metricHitRate", d.localHitRate);
    }
  },

  async performSearch(query, assetType = "") {
    const tbody = document.getElementById("assetSearchResultsBody");
    if (!tbody) return;

    if (!query) {
      query = "B0"; // Default seed search
    }

    tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-400 text-xs">正在搜索本地仓库资产...</td></tr>`;

    const res = await API.searchAssets(query, assetType || null);
    const items = (res.status === "ok" && res.data) ? res.data : [];

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-400 text-xs">本地仓库暂无匹配 "${query}" 的资产，可通过“数据采集中心”调取并沉淀入库。</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map((it) => {
      const typeBadge = {
        asin: '<span class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">ASIN商品</span>',
        keyword: '<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200">关键词</span>',
        top100: '<span class="px-2 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-bold border border-purple-200">类目榜单</span>',
        raw_response: '<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">原始报文</span>'
      }[it.asset_type] || `<span class="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px]">${it.asset_type}</span>`;

      const actionBtn = (it.asset_type === "raw_response" || it.raw_id) ? 
        `<button onclick="DataAssets.viewRawModal(${it.raw_id || it.id.replace('RAW-', '')})" class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-semibold transition">查看原始报文</button>` :
        `<button onclick="DataAssets.searchRelated('${it.id}')" class="px-2.5 py-1 rounded bg-blue-50 hover:bg-blue-100 text-blue-700 text-[11px] font-semibold transition">溯源流水</button>`;

      return `
        <tr class="border-b border-slate-100 hover:bg-slate-50/50 transition">
          <td class="py-3 px-4 font-mono font-bold text-slate-900 text-xs">${it.id}</td>
          <td class="py-3 px-4">${typeBadge}</td>
          <td class="py-3 px-4 text-slate-800 text-xs font-medium max-w-xs truncate" title="${it.title}">${it.title}</td>
          <td class="py-3 px-4 font-mono text-blue-600 text-xs font-bold">${it.metric_primary}</td>
          <td class="py-3 px-4 text-slate-500 text-[11px] font-mono">${it.date}</td>
          <td class="py-3 px-4 text-right">${actionBtn}</td>
        </tr>
      `;
    }).join("");
  },

  searchRelated(query) {
    const input = document.getElementById("inputSearchAssets");
    if (input) {
      input.value = query;
      this.performSearch(query);
    }
  },

  async viewRawModal(rawId) {
    const modal = document.getElementById("rawModal");
    const title = document.getElementById("rawModalTitle");
    const jsonContent = document.getElementById("rawModalContent");
    if (!modal) return;

    modal.classList.remove("hidden");
    if (title) title.textContent = `原始 MCP 响应留痕 #${rawId} (Immutable Evidence)`;
    if (jsonContent) jsonContent.textContent = "正在加载原始不可篡改报文...";

    const res = await API.getRawAsset(rawId);
    if (res.status === "ok" && res.data) {
      if (jsonContent) {
        jsonContent.textContent = JSON.stringify(res.data, null, 2);
      }
    } else {
      if (jsonContent) {
        jsonContent.textContent = `无法加载报文: ${res.message || "记录不存在"}`;
      }
    }
  },

  closeRawModal() {
    const modal = document.getElementById("rawModal");
    if (modal) modal.classList.add("hidden");
  }
};
