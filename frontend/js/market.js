// Market View Controller (Module 1)
const MarketView = {
  currentNodeId: "1055398:1063252:1199122:3732111",

  async init() {
    await this.loadTree();
    await this.loadMarketData(this.currentNodeId);
  },

  async loadTree() {
    const res = await API.getMarketTree();
    if (!res || res.status !== "ok" || !res.data) return;

    const subcats = res.data.subcategories || [];
    const container = document.getElementById("marketSubcatTabs");
    if (!container) return;

    container.innerHTML = subcats.map(sub => `
      <button onclick="MarketView.switchSubcategory('${sub.nodeIdPath}')" 
        class="market-subcat-btn px-3 py-1.5 rounded-md text-xs font-medium border transition ${sub.nodeIdPath === this.currentNodeId ? 'bg-blue-50 text-blue-600 border-blue-200' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}">
        ${sub.nodeLabel}
      </button>
    `).join("");
  },

  async switchSubcategory(nodeId) {
    this.currentNodeId = nodeId;
    document.querySelectorAll(".market-subcat-btn").forEach(btn => {
      btn.className = "market-subcat-btn px-3 py-1.5 rounded-md text-xs font-medium border transition bg-white text-slate-600 border-slate-200 hover:bg-slate-50";
    });
    // highlight current
    await this.loadMarketData(nodeId);
  },

  async loadMarketData(nodeIdPath) {
    const loading = document.getElementById("marketLoading");
    if (loading) loading.classList.remove("hidden");

    const res = await API.getMarketOverview(nodeIdPath);
    if (loading) loading.classList.add("hidden");

    const emptyBox = document.getElementById("marketEmptyState");
    const contentBox = document.getElementById("marketContent");

    if (!res || res.status !== "ok" || !res.data) {
      if (emptyBox) emptyBox.classList.remove("hidden");
      if (contentBox) contentBox.classList.add("hidden");
      return;
    }

    if (emptyBox) emptyBox.classList.add("hidden");
    if (contentBox) contentBox.classList.remove("hidden");

    const d = res.data;

    // KPI row
    document.getElementById("mktProducts").textContent = (d.totalProducts || 0).toLocaleString();
    document.getElementById("mktUnits").textContent = (d.totalUnits || 0).toLocaleString();
    document.getElementById("mktRevenue").textContent = d.totalRevenue ? `$${d.totalRevenue.toLocaleString()}` : "--";
    document.getElementById("mktCr4").textContent = `${d.cr4 || 0}%`;
    document.getElementById("mktMonopolyStatus").textContent = d.monopolyStatus || "分析中";

    // Charts
    Charts.renderPriceBrackets("chartMarketPriceBrackets", d.priceBrackets || []);

    // Brand Concentration Table
    const brandTbody = document.getElementById("mktBrandTableBody");
    if (brandTbody) {
      brandTbody.innerHTML = (d.brandRankings || []).map(b => `
        <tr class="hover:bg-slate-50 text-xs border-b border-slate-100">
          <td class="py-2.5 px-3 font-mono text-slate-500 font-bold">#${b.ranking}</td>
          <td class="py-2.5 px-3 font-bold text-slate-900">${b.name}</td>
          <td class="py-2.5 px-3 font-mono font-semibold text-blue-600">${b.share}%</td>
          <td class="py-2.5 px-3 font-mono">${b.units ? b.units.toLocaleString() : '--'}</td>
          <td class="py-2.5 px-3 font-mono">${b.avgPrice ? `$${b.avgPrice}` : '--'}</td>
        </tr>
      `).join("");
    }
  }
};
