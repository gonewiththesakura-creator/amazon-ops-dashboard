// Core Products (4 SKUs) War Room Controller (Module 2 - V2.1)
const ProductsView = {
  currentAsin: "B0GYH8WT22",
  competitorData: null,
  activePool: "direct",

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
        class="sku-tab-btn px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${p.asin === this.currentAsin ? 'bg-blue-600 text-white border-blue-600 shadow-sm' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}">
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

    const [detailRes, compRes] = await Promise.all([
      API.getProductDetail(asin),
      API.getProductCompetitors(asin)
    ]);
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

    // 2. Metrics Header & Diagnosis
    document.getElementById("prodTitle").textContent = d.title || d.internalName || asin;
    document.getElementById("prodAsin").textContent = `ASIN: ${asin}`;
    document.getElementById("prodBrand").textContent = d.brand || "ELOVNOVA";
    document.getElementById("prodParent").textContent = d.parentAsin || "无 (独立单品)";
    
    const couponEl = document.getElementById("prodCoupon");
    if (couponEl) {
      couponEl.textContent = `Coupon: ${d.coupon || '无'}`;
    }

    const linkEl = document.getElementById("prodLink");
    if (linkEl) linkEl.href = d.productUrl || `https://www.amazon.com/dp/${asin}`;

    // Plain Diagnosis Banner
    const diagEl = document.getElementById("prodPlainDiagnosis");
    if (diagEl) {
      diagEl.textContent = d.plainDiagnosis || "正在运行规则系统进行综合研判...";
    }

    // Pricing & BSR Scalar Values
    document.getElementById("prodPrice").textContent = d.price ? `$${d.price}` : "暂无标价";
    
    const priceStatusEl = document.getElementById("prodPriceStatus");
    if (priceStatusEl) {
      if (!d.hasPriceChanged) {
        priceStatusEl.textContent = d.lastPriceChange || "标价持续稳定 (无改价记录)";
        priceStatusEl.className = "text-[10px] text-emerald-600 font-medium mt-1 truncate";
      } else {
        priceStatusEl.textContent = d.lastPriceChange || "近期存在价格调整";
        priceStatusEl.className = "text-[10px] text-amber-600 font-medium mt-1 truncate";
      }
    }

    // BSR Formatting (Clean scalar!)
    const bsrFormatted = (d.bsr && typeof d.bsr === "number" && d.bsr > 0)
      ? `#${d.bsr.toLocaleString()}`
      : "暂无大类BSR";
    document.getElementById("prodBsr").textContent = bsrFormatted;

    document.getElementById("prodRating").textContent = d.rating ? `${d.rating} ★ (${d.ratingsCount ? d.ratingsCount.toLocaleString() : 0})` : "--";
    
    const ratingStatusEl = document.getElementById("prodRatingStatus");
    if (ratingStatusEl) {
      if (d.rating && d.rating >= 4.2) {
        ratingStatusEl.textContent = "口碑评分处于健康区间";
        ratingStatusEl.className = "text-[10px] text-emerald-600 font-medium mt-1";
      } else if (d.rating && d.rating < 4.0) {
        ratingStatusEl.textContent = "评分低于4.0需重点优化痛点";
        ratingStatusEl.className = "text-[10px] text-rose-600 font-medium mt-1";
      } else {
        ratingStatusEl.textContent = "真实买家反馈累积中";
        ratingStatusEl.className = "text-[10px] text-slate-500 mt-1";
      }
    }

    const snapHistoryEl = document.getElementById("prodSnapshotHistory");
    if (snapHistoryEl) {
      snapHistoryEl.textContent = d.trend30dLabel || "从今天开始监控";
    }

    // 3. Render Independent Split Charts (Step Chart for Price + Trend Chart for BSR)
    Charts.renderPriceStepChart("chartProdPriceStep", d.priceStepPoints || [], {
      lastPriceChange: d.lastPriceChange,
      hasPriceChanged: d.hasPriceChanged
    });

    Charts.renderSalesBsrChart("chartProdBsrTrend", d.bsrTrendPoints || []);

    // 4. Competitors
    this.competitorData = compRes.data || {};
    this.updateCompetitorBadges();
    this.switchCompetitorPool(this.activePool || "direct");
  },

  updateCompetitorBadges() {
    if (!this.competitorData) return;
    const directCount = (this.competitorData.directCompetitors || []).length;
    const suggestedCount = (this.competitorData.suggestedCompetitors || []).length;
    const topCount = (this.competitorData.top100Pool || []).length;

    const bDirect = document.getElementById("badgeDirectCount");
    if (bDirect) bDirect.textContent = directCount;

    const bSuggested = document.getElementById("badgeSuggestedCount");
    if (bSuggested) bSuggested.textContent = suggestedCount;

    const bTop = document.getElementById("badgeTopCount");
    if (bTop) bTop.textContent = topCount;

    // Show/hide direct competitor empty state notice
    const emptyNotice = document.getElementById("directCompEmptyNotice");
    const emptyCountEl = document.getElementById("emptySuggestedCount");
    if (emptyNotice) {
      if (directCount === 0) {
        emptyNotice.classList.remove("hidden");
        if (emptyCountEl) emptyCountEl.textContent = suggestedCount;
      } else {
        emptyNotice.classList.add("hidden");
      }
    }
  },

  switchCompetitorPool(poolType) {
    this.activePool = poolType;

    document.querySelectorAll(".comp-pool-btn").forEach(btn => {
      btn.className = "comp-pool-btn px-2.5 py-1 rounded text-xs font-medium text-slate-600 hover:text-slate-900 transition";
    });
    const activeBtn = document.getElementById(`btnPool-${poolType}`);
    if (activeBtn) {
      activeBtn.className = "comp-pool-btn px-2.5 py-1 rounded text-xs font-semibold bg-white text-blue-600 shadow-sm transition";
    }

    const tbody = document.getElementById("compTableBody");
    if (!tbody || !this.competitorData) return;

    let list = [];
    if (poolType === "direct") list = this.competitorData.directCompetitors || [];
    else if (poolType === "suggested") list = this.competitorData.suggestedCompetitors || [];
    else if (poolType === "benchmark") list = this.competitorData.benchmarkCompetitors || [];
    else list = this.competitorData.top100Pool || [];

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400 text-xs">
        <div class="text-xl mb-1">🔍</div>
        <div>暂无该分类竞品数据</div>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(c => {
      const gap = c.gap || {};
      const gapSummary = gap.summary || "正在测算中";
      const gapInsight = gap.insight || "维持正常观察";

      let actionHtml = "";
      if (poolType === "suggested") {
        actionHtml = `
          <button onclick="ProductsView.confirmSuggestedCompetitor('${c.asin}')" class="px-2 py-1 rounded bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-[11px] transition shadow-xs">
            + 设为直接竞品
          </button>
        `;
      } else if (poolType === "direct") {
        actionHtml = `
          <button onclick="ProductsView.removeCompetitor('${c.asin}')" class="px-2 py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 font-medium text-[11px] transition">
            移除
          </button>
        `;
      } else {
        actionHtml = `
          <button onclick="ProductsView.confirmSuggestedCompetitor('${c.asin}')" class="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] transition">
            + 关注
          </button>
        `;
      }

      return `
        <tr class="hover:bg-slate-50/80 text-xs border-b border-slate-100 transition">
          <td class="py-3 px-3">
            <div class="flex items-center gap-2">
              <div>
                <div class="font-mono font-bold text-blue-600 flex items-center gap-1.5">
                  <span>${c.asin}</span>
                  ${c.badge ? `<span class="text-[9px] px-1.5 py-0.2 rounded font-sans font-normal ${c.verified ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'}">${c.badge}</span>` : ''}
                </div>
                <div class="text-slate-900 font-medium line-clamp-1 max-w-xs mt-0.5" title="${c.title}">${c.title}</div>
                <div class="text-[10px] text-slate-400">品牌: ${c.brand || 'N/A'}</div>
              </div>
            </div>
          </td>
          <td class="py-3 px-3 font-mono font-bold text-amber-600">${c.price ? `$${c.price}` : '<span class="text-slate-400">--</span>'}</td>
          <td class="py-3 px-3 font-mono text-slate-600">${c.bsr ? `#${Number(c.bsr).toLocaleString()}` : '<span class="text-slate-400">--</span>'}</td>
          <td class="py-3 px-3 font-mono">${c.monthlyUnits ? c.monthlyUnits.toLocaleString() : '<span class="text-slate-400">--</span>'}</td>
          <td class="py-3 px-3 font-mono">
            ${c.rating ? `<span class="font-bold text-slate-800">${c.rating}★</span> <span class="text-slate-400 text-[10px]">(${c.ratingsCount ? c.ratingsCount.toLocaleString() : 0})</span>` : '<span class="text-slate-400">--</span>'}
          </td>
          <td class="py-3 px-3">
            <div class="text-slate-800 font-medium text-[11px]">${gapSummary}</div>
            <div class="text-[10px] text-blue-600 mt-0.5">${gapInsight}</div>
          </td>
          <td class="py-3 px-3 text-right">
            <div class="flex items-center justify-end gap-1.5">
              ${actionHtml}
              <a href="${c.url}" target="_blank" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition" title="在亚马逊打开">
                ↗
              </a>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  },

  // Modal Handlers
  openAddCompetitorModal() {
    const modal = document.getElementById("modalAddCompetitor");
    if (modal) {
      modal.classList.remove("hidden");
      document.getElementById("inputManualCompAsin").value = "";
      document.getElementById("inputManualCompNotes").value = "";
    }
  },

  closeAddCompetitorModal() {
    const modal = document.getElementById("modalAddCompetitor");
    if (modal) modal.classList.add("hidden");
  },

  async submitManualCompetitor() {
    const asinInput = document.getElementById("inputManualCompAsin");
    const notesInput = document.getElementById("inputManualCompNotes");
    const compAsin = (asinInput.value || "").trim().toUpperCase();
    const notes = (notesInput.value || "").trim() || "手工添加直接竞品";

    if (!compAsin || compAsin.length < 5) {
      alert("请输入有效的竞品 ASIN！");
      return;
    }

    const btn = document.getElementById("btnSubmitManualComp");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "添加中...";
    }

    const res = await API.addManualCompetitor(this.currentAsin, compAsin, notes);
    if (btn) {
      btn.disabled = false;
      btn.textContent = "确认添加";
    }

    if (res && res.status === "ok") {
      this.closeAddCompetitorModal();
      this.activePool = "direct";
      await this.loadProduct(this.currentAsin);
    } else {
      alert(`添加竞品失败: ${res?.error || '未知错误'}`);
    }
  },

  async confirmSuggestedCompetitor(compAsin) {
    const res = await API.confirmCompetitor(this.currentAsin, compAsin);
    if (res && res.status === "ok") {
      this.activePool = "direct";
      await this.loadProduct(this.currentAsin);
    } else {
      alert(`确认直接竞品失败: ${res?.error || '未知错误'}`);
    }
  },

  async removeCompetitor(compAsin) {
    if (!confirm(`确定要从直接竞品池中移除 ${compAsin} 吗？`)) return;
    const res = await API.deleteCompetitor(this.currentAsin, compAsin);
    if (res && res.status === "ok") {
      await this.loadProduct(this.currentAsin);
    } else {
      alert(`移除竞品失败: ${res?.error || '未知错误'}`);
    }
  }
};

