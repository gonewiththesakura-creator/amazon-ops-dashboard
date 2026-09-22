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
    this.renderBossCompetitorCard();
    this.renderBenchmarkInsightCard();

    // Render Boss Charts (Horizontal Bar + Scatter Plot)
    if (this.competitorData?.scatterData) {
      Charts.renderCompetitorScatter("chartCompetitorScatter", this.competitorData.scatterData || []);
    }
    const directForBar = [
      {
        asin: asin,
        brand: `${d.brand || 'ELOVNOVA'} (我方)`,
        isOur: true,
        monthlyUnits: d.monthlyUnits || 0,
        price: d.price,
        rating: d.rating,
        reviews: d.ratingsCount,
        metricScope: "child_asin"
      },
      ...(this.competitorData?.directCompetitors || []).map(c => ({
        asin: c.asin,
        brand: c.brand || c.asin,
        isOur: false,
        monthlyUnits: c.monthlyUnits || 0,
        price: c.price,
        rating: c.rating,
        reviews: c.ratingsCount,
        whyCompetitor: c.whyCompetitor,
        metricScope: c.metricScope
      }))
    ];
    Charts.renderCompetitorHorizontalBar("chartCompetitorHorizontalBar", directForBar);

    this.switchCompetitorPool(this.activePool || "direct");
  },

  renderBossCompetitorCard() {
    if (!this.competitorData) return;
    const bs = this.competitorData.bossSummary || {};
    const directCount = (this.competitorData.directCompetitors || []).length;

    const statusBadge = document.getElementById("bossCompStatusBadge");
    if (statusBadge) {
      statusBadge.textContent = directCount > 0
        ? `已对标 ${directCount} 款直接竞品`
        : "尚未锁定直接竞品";
      statusBadge.className = directCount > 0
        ? "px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-700"
        : "px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-700";
    }

    const challengeEl = document.getElementById("bossCompPrimaryChallenge");
    if (challengeEl) {
      challengeEl.textContent = bs.primaryChallenge || "正在综合对比我方与直接竞品参数...";
    }

    const gaps = bs.top3Gaps || [];
    const g1 = document.getElementById("bossGap1");
    const g2 = document.getElementById("bossGap2");
    const g3 = document.getElementById("bossGap3");
    if (g1) g1.textContent = gaps[0] || "--";
    if (g2) g2.textContent = gaps[1] || "--";
    if (g3) g3.textContent = gaps[2] || "--";

    const actionsEl = document.getElementById("bossCompActions");
    if (actionsEl && bs.recommendedActions) {
      actionsEl.innerHTML = bs.recommendedActions.map(a => `<div>• ${a}</div>`).join("");
    }
  },

  renderBenchmarkInsightCard() {
    const card = document.getElementById("benchmarkInsightCard");
    if (!card) return;
    const bi = this.competitorData?.benchmarkInsight;
    if (!bi || bi.benchmarkCount === 0) {
      card.classList.add("hidden");
      return;
    }

    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-sm">🏆</span>
            <span class="font-bold text-slate-900 text-xs">头部标杆告诉我们什么？(细分市场天花板洞察)</span>
            <span class="px-2 py-0.2 rounded bg-amber-100 text-amber-800 text-[10px] font-bold">已剔除配件/按Parent去重</span>
          </div>
          <p class="text-xs text-slate-700 leading-relaxed font-medium mt-1">
            ${bi.ceilingConclusion}
          </p>
        </div>
        <div class="flex items-center gap-3 text-center flex-shrink-0 bg-white/70 px-3 py-1.5 rounded-lg border border-amber-200">
          <div>
            <div class="text-[9px] text-slate-400">头部均销</div>
            <div class="text-xs font-bold font-mono text-blue-600">${bi.avgUnits ? bi.avgUnits.toLocaleString() + ' 件' : '--'}</div>
          </div>
          <div class="border-l border-amber-200 pl-3">
            <div class="text-[9px] text-slate-400">主流售价区间</div>
            <div class="text-xs font-bold font-mono text-amber-700">${bi.priceRange}</div>
          </div>
          <div class="border-l border-amber-200 pl-3">
            <div class="text-[9px] text-slate-400">Review中位数</div>
            <div class="text-xs font-bold font-mono text-slate-800">${bi.medianReviews ? bi.medianReviews.toLocaleString() + ' 条' : '--'}</div>
          </div>
        </div>
      </div>
    `;
    if (this.activePool === "benchmark") {
      card.classList.remove("hidden");
    } else {
      card.classList.add("hidden");
    }
  },

  updateCompetitorBadges() {
    if (!this.competitorData) return;
    const directCount = (this.competitorData.directCompetitors || []).length;
    const suggestedCount = (this.competitorData.suggestedCompetitors || []).length;
    const benchCount = (this.competitorData.benchmarkCompetitors || []).length;
    const topCount = (this.competitorData.top100Pool || []).length;

    const bDirect = document.getElementById("badgeDirectCount");
    if (bDirect) bDirect.textContent = directCount;

    const bSuggested = document.getElementById("badgeSuggestedCount");
    if (bSuggested) bSuggested.textContent = suggestedCount;

    const bBench = document.getElementById("badgeBenchmarkCount");
    if (bBench) bBench.textContent = benchCount;

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

    // Toggle benchmark insight card visibility
    const benchCard = document.getElementById("benchmarkInsightCard");
    if (benchCard) {
      if (poolType === "benchmark" && this.competitorData?.benchmarkInsight?.benchmarkCount > 0) {
        benchCard.classList.remove("hidden");
      } else {
        benchCard.classList.add("hidden");
      }
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
          <div class="flex items-center justify-end gap-1.5">
            <button onclick="ProductsView.confirmSuggestedCompetitor('${c.asin}')" class="px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold text-[11px] transition shadow-xs">
              + 加入直接竞品
            </button>
            <button onclick="ProductsView.ignoreCandidateCompetitor('${c.asin}')" class="px-2 py-1 rounded bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 font-medium text-[11px] transition" title="不再推荐此候选">
              忽略
            </button>
          </div>
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

      // Variation duplicate warning badge
      const isParentDuplicate = c.isVariationFamilyDuplicate || c.metricScope === 'parent_family';
      const duplicateNotice = isParentDuplicate ? `
        <div class="mt-1 px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-[10px] text-amber-800 flex items-center gap-1 font-sans">
          <span>⚠️</span>
          <span>父体聚合数据（禁止与同品牌变体重复计入）</span>
        </div>
      ` : '';

      // Suggested similarity badge
      const simBadge = (poolType === 'suggested' && c.similarityScore) ? `
        <span class="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
          ${c.similarityScore}% 相似
        </span>
      ` : '';

      // Detailed gap / why competitor column
      let reasoningHtml = "";
      if (poolType === 'direct') {
        reasoningHtml = `
          <div>
            ${c.whyCompetitor ? `<div class="text-[11px] font-bold text-slate-900">${c.whyCompetitor}</div>` : ''}
            <div class="text-slate-700 text-[11px] mt-0.5">${gapSummary}</div>
            <div class="text-[10px] text-blue-600 font-medium mt-0.5">${gapInsight}</div>
            ${duplicateNotice}
          </div>
        `;
      } else if (poolType === 'suggested') {
        reasoningHtml = `
          <div>
            <div class="text-[11px] font-bold text-slate-800">${c.similarityReason || '同品类潜在对标款'}</div>
            <div class="text-[10px] text-slate-500 mt-0.5">${gapSummary}</div>
          </div>
        `;
      } else {
        reasoningHtml = `
          <div>
            <div class="text-slate-800 font-medium text-[11px]">${gapSummary}</div>
            <div class="text-[10px] text-blue-600 mt-0.5">${gapInsight}</div>
          </div>
        `;
      }

      const estUnits = c.sellerSpriteEstimatedMonthlyUnits || c.monthlyUnits;

      return `
        <tr class="hover:bg-slate-50/80 text-xs border-b border-slate-100 transition">
          <td class="py-3 px-3">
            <div class="flex items-center gap-2">
              <div>
                <div class="font-mono font-bold text-blue-600 flex items-center gap-1.5">
                  <span>${c.asin}</span>
                  ${simBadge}
                  ${c.badge ? `<span class="text-[9px] px-1.5 py-0.2 rounded font-sans font-normal ${c.verified ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'}">${c.badge}</span>` : ''}
                </div>
                <div class="text-slate-900 font-medium line-clamp-1 max-w-xs mt-0.5" title="${c.title}">${c.title}</div>
                <div class="text-[10px] text-slate-400">品牌: ${c.brand || 'N/A'} ${c.parentAsin ? `| Parent: ${c.parentAsin}` : ''}</div>
              </div>
            </div>
          </td>
          <td class="py-3 px-3 font-mono font-bold text-amber-600">${c.price ? `$${c.price}` : '<span class="text-slate-400">--</span>'}</td>
          <td class="py-3 px-3 font-mono text-slate-600">${c.bsr ? `#${Number(c.bsr).toLocaleString()}` : '<span class="text-slate-400">--</span>'}</td>
          <td class="py-3 px-3 font-mono">
            <div title="数据源: 卖家精灵第三方月度估算" class="cursor-help">
              <span class="font-bold text-slate-900">${estUnits ? estUnits.toLocaleString() + ' 件' : '<span class="text-slate-400">--</span>'}</span>
              <div class="text-[9px] text-slate-400">卖家精灵预估</div>
            </div>
          </td>
          <td class="py-3 px-3 font-mono">
            ${c.rating ? `<span class="font-bold text-slate-800">${c.rating}★</span> <span class="text-slate-400 text-[10px]">(${(c.ratingsCount || 0).toLocaleString()})</span>` : '<span class="text-slate-400">--</span>'}
          </td>
          <td class="py-3 px-3">
            ${reasoningHtml}
          </td>
          <td class="py-3 px-3 text-right">
            <div class="flex items-center justify-end gap-1.5">
              ${actionHtml}
              <a href="${c.url}" target="_blank" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition" title="在亚马逊打开 Listing">
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
      alert(`⚠️ 添加直接竞品失败：\n${res?.error || res?.detail || 'ASIN 无效或在亚马逊美国站不存在，已拒绝添加。'}`);
    }
  },

  async confirmSuggestedCompetitor(compAsin) {
    const res = await API.confirmCompetitor(this.currentAsin, compAsin);
    if (res && res.status === "ok") {
      this.activePool = "direct";
      await this.loadProduct(this.currentAsin);
    } else {
      alert(`⚠️ 确认直接竞品失败：\n${res?.error || res?.detail || 'ASIN 验证未通过。'}`);
    }
  },

  async ignoreCandidateCompetitor(compAsin) {
    const res = await API.ignoreCompetitor(this.currentAsin, compAsin);
    if (res && res.status === "ok") {
      await this.loadProduct(this.currentAsin);
    } else {
      alert(`忽略竞品失败: ${res?.error || '未知错误'}`);
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

