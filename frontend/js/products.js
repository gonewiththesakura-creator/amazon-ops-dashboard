// Core Products (4 SKUs) War Room Controller (Module 2)
const ProductsView = {
  currentAsin: "B0GYH8WT22",
  competitorData: null,

  async init(targetAsin) {
    if (targetAsin) {
      this.currentAsin = targetAsin;
    }
    await this.renderSkuSelector();
    await this.loadProduct(this.currentAsin);
  },

  async renderSkuSelector() {
    const res = await API.getCoreProducts();
    if (!res || res.status !== "ok" || !res.data) return;

    const container = document.getElementById("productSkuTabs");
    if (!container) return;

    container.innerHTML = res.data.map(p => `
      <button onclick="ProductsView.switchSku('${p.asin}')"
        class="sku-tab-btn px-3 py-1.5 rounded-md text-xs font-semibold border transition ${p.asin === this.currentAsin ? 'bg-blue-600 text-white border-blue-600 shadow-sm' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}">
        ${p.internal_name} (${p.asin})
      </button>
    `).join("");
  },

  async switchSku(asin) {
    this.currentAsin = asin;
    await this.renderSkuSelector();
    await this.loadProduct(asin);
  },

  async loadProduct(asin) {
    const loading = document.getElementById("productLoading");
    if (loading) loading.classList.remove("hidden");

    const detailRes = await API.getProductDetail(asin);
    const compRes = await API.getProductCompetitors(asin);
    if (loading) loading.classList.add("hidden");

    const d = detailRes.data || {};

    // 1. Pending SKU Check
    const pendingBox = document.getElementById("productPendingNotice");
    const activeBox = document.getElementById("productActiveContent");

    if (asin === "PENDING_SKU_4") {
      if (pendingBox) pendingBox.classList.remove("hidden");
      if (activeBox) activeBox.classList.add("hidden");
      return;
    }

    if (pendingBox) pendingBox.classList.add("hidden");
    if (activeBox) activeBox.classList.remove("hidden");

    // 2. Metrics Header
    document.getElementById("prodTitle").textContent = d.title || d.internalName || asin;
    document.getElementById("prodAsin").textContent = `ASIN: ${asin}`;
    document.getElementById("prodBrand").textContent = d.brand || "ELOVNOVA";
    document.getElementById("prodPrice").textContent = d.price ? `$${d.price}` : "暂无标价";
    
    // BSR Formatting (Clean scalar!)
    const bsrFormatted = (d.bsr && typeof d.bsr === "number" && d.bsr > 0)
      ? `#${d.bsr.toLocaleString()}`
      : "暂无大类BSR";
    document.getElementById("prodBsr").textContent = bsrFormatted;

    document.getElementById("prodRating").textContent = d.rating ? `${d.rating} ★ (${d.ratingsCount || 0})` : "--";
    document.getElementById("prodParent").textContent = d.parentAsin || "无 (独立单品)";
    
    const linkEl = document.getElementById("prodLink");
    if (linkEl) linkEl.href = d.productUrl || `https://www.amazon.com/dp/${asin}`;

    // 3. Render Trend Chart (If real points exist)
    Charts.renderPriceBSR("chartProdHistory", d.timeline || [], d.prices || [], d.bsrs || []);

    // 4. Competitors
    this.competitorData = compRes.data || {};
    this.switchCompetitorPool("direct");
  },

  switchCompetitorPool(poolType) {
    document.querySelectorAll(".comp-pool-btn").forEach(btn => {
      btn.className = "comp-pool-btn px-3 py-1.5 rounded-md text-xs font-medium border border-slate-200 bg-white text-slate-600 hover:bg-slate-50";
    });
    const activeBtn = document.getElementById(`btnPool-${poolType}`);
    if (activeBtn) {
      activeBtn.className = "comp-pool-btn px-3 py-1.5 rounded-md text-xs font-semibold border border-blue-200 bg-blue-50 text-blue-600";
    }

    const tbody = document.getElementById("compTableBody");
    if (!tbody || !this.competitorData) return;

    let list = [];
    if (poolType === "direct") list = this.competitorData.directCompetitors || [];
    else if (poolType === "benchmark") list = this.competitorData.benchmarkCompetitors || [];
    else if (poolType === "fast_growth") list = this.competitorData.fastGrowthCompetitors || [];
    else list = this.competitorData.top100Pool || [];

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400 text-xs">暂无该分类竞品数据</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(c => `
      <tr class="hover:bg-slate-50 text-xs border-b border-slate-100">
        <td class="py-2.5 px-3 font-mono font-bold text-blue-600">${c.asin}</td>
        <td class="py-2.5 px-3 text-slate-900 font-medium max-w-xs truncate" title="${c.title}">${c.title}</td>
        <td class="py-2.5 px-3 text-slate-600">${c.brand}</td>
        <td class="py-2.5 px-3 font-mono font-bold text-amber-600">${c.price ? `$${c.price}` : '--'}</td>
        <td class="py-2.5 px-3 font-mono text-slate-600">${c.bsr ? `#${Number(c.bsr).toLocaleString()}` : '--'}</td>
        <td class="py-2.5 px-3 font-mono">${c.monthlyUnits ? c.monthlyUnits.toLocaleString() : '--'}</td>
        <td class="py-2.5 px-3 text-right">
          <a href="${c.url}" target="_blank" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition">
            Amazon ↗
          </a>
        </td>
      </tr>
    `).join("");
  }
};
