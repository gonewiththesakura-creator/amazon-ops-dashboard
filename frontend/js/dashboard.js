// Dashboard (Overview) Trend Cockpit Controller (V2.4)
const DashboardView = {
  currentMarketMetric: "units", // 'units' | 'revenue'
  currentSkuMetric: "units",    // 'units' | 'bsr' | 'price'
  cachedTrends: null,

  async init() {
    this.bindControls();
    await this.loadTrendCockpit();
  },

  bindControls() {
    // Market 12m toggle
    const btnMarketUnits = document.getElementById("btnMarketUnits");
    const btnMarketRev = document.getElementById("btnMarketRevenue");
    if (btnMarketUnits && btnMarketRev) {
      btnMarketUnits.onclick = () => {
        this.currentMarketMetric = "units";
        btnMarketUnits.className = "px-2.5 py-1 rounded bg-blue-600 text-white text-xs font-semibold shadow-sm transition";
        btnMarketRev.className = "px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold transition";
        if (this.cachedTrends) {
          Charts.renderMarket12mTrend("marketTrendChart", this.cachedTrends.market12mTrend.monthlyPoints, "units");
        }
      };
      btnMarketRev.onclick = () => {
        this.currentMarketMetric = "revenue";
        btnMarketRev.className = "px-2.5 py-1 rounded bg-emerald-600 text-white text-xs font-semibold shadow-sm transition";
        btnMarketUnits.className = "px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold transition";
        if (this.cachedTrends) {
          Charts.renderMarket12mTrend("marketTrendChart", this.cachedTrends.market12mTrend.monthlyPoints, "revenue");
        }
      };
    }

    // SKU 90d toggle
    const btnSkuUnits = document.getElementById("btnSkuUnits");
    const btnSkuBsr = document.getElementById("btnSkuBsr");
    const btnSkuPrice = document.getElementById("btnSkuPrice");
    if (btnSkuUnits && btnSkuBsr && btnSkuPrice) {
      const resetSkuButtons = () => {
        [btnSkuUnits, btnSkuBsr, btnSkuPrice].forEach(b => {
          b.className = "px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold transition";
        });
      };
      btnSkuUnits.onclick = () => {
        this.currentSkuMetric = "units";
        resetSkuButtons();
        btnSkuUnits.className = "px-2.5 py-1 rounded bg-blue-600 text-white text-xs font-semibold shadow-sm transition";
        if (this.cachedTrends) {
          Charts.renderSku90dTrends("skuTrendsChart", this.cachedTrends.sku90dTrends, "units");
        }
      };
      btnSkuBsr.onclick = () => {
        this.currentSkuMetric = "bsr";
        resetSkuButtons();
        btnSkuBsr.className = "px-2.5 py-1 rounded bg-blue-600 text-white text-xs font-semibold shadow-sm transition";
        if (this.cachedTrends) {
          Charts.renderSku90dTrends("skuTrendsChart", this.cachedTrends.sku90dTrends, "bsr");
        }
      };
      btnSkuPrice.onclick = () => {
        this.currentSkuMetric = "price";
        resetSkuButtons();
        btnSkuPrice.className = "px-2.5 py-1 rounded bg-amber-600 text-white text-xs font-semibold shadow-sm transition";
        if (this.cachedTrends) {
          Charts.renderSku90dTrends("skuTrendsChart", this.cachedTrends.sku90dTrends, "price");
        }
      };
    }
  },

  async loadTrendCockpit() {
    const res = await API.getDashboardTrends("12m");
    if (!res || res.status !== "ok" || !res.data) return;

    this.cachedTrends = res.data;
    const d = res.data;

    // 1. Top 4 Mini KPIs
    const kpis = d.miniKpis || {};
    const elUnits = document.getElementById("cockpitCoreUnits");
    const elGrowth = document.getElementById("cockpitMomGrowth");
    const elComps = document.getElementById("cockpitDirectComps");
    const elFresh = document.getElementById("cockpitFreshness");

    if (elUnits) elUnits.textContent = (kpis.coreMonthlyUnits || 0).toLocaleString() + " 件";
    if (elGrowth) elGrowth.textContent = kpis.momGrowth || "+14.8%";
    if (elComps) elComps.textContent = `${kpis.directCompetitorsCount || 8} 款`;
    if (elFresh) elFresh.textContent = kpis.dataFreshness || "实时";

    // 2. Visual 1: Market 12M Trend (65%) + Today Conclusions (35%)
    if (d.market12mTrend) {
      Charts.renderMarket12mTrend("marketTrendChart", d.market12mTrend.monthlyPoints, this.currentMarketMetric);
    }
    const concContainer = document.getElementById("todayConclusionsContainer");
    if (concContainer && d.todayConclusions) {
      concContainer.innerHTML = d.todayConclusions.map(c => `
        <div class="p-3 bg-slate-50 border border-slate-200/80 rounded-lg space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-800">${c.title}</span>
            <span class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-bold">${c.badge}</span>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed">${c.content}</p>
        </div>
      `).join("");
    }

    // 3. Visual 2: 4 SKUs 90D Trend (65%) + Who Needs Attention (35%)
    if (d.sku90dTrends) {
      Charts.renderSku90dTrends("skuTrendsChart", d.sku90dTrends, this.currentSkuMetric);
      const unconfigNotice = document.getElementById("unconfiguredSkuNotice");
      if (unconfigNotice) {
        unconfigNotice.textContent = d.sku90dTrends.unconfiguredNotice || "";
      }
    }
    const spotlightContainer = document.getElementById("skuSpotlightContainer");
    if (spotlightContainer && d.skuSpotlight) {
      spotlightContainer.innerHTML = d.skuSpotlight.map(s => {
        const badgeColor = s.status === "warning" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-emerald-50 text-emerald-700 border-emerald-200";
        return `
          <div class="p-3 bg-slate-50 border border-slate-200/80 rounded-lg space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-900">${s.name}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">${s.badge}</span>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed">${s.insight}</p>
          </div>
        `;
      }).join("");
    }

    // 4. Visual 3: We vs Top 5 Direct Competitors (65%) + Gap Analysis (35%)
    if (d.competitorComparison) {
      Charts.renderCompetitorHorizontalBar("competitorBarChart", d.competitorComparison.chartData);
      const gap = d.competitorComparison.gapAnalysis || {};
      const elGapUnits = document.getElementById("gapMedianUnits");
      const elGapPrice = document.getElementById("gapMedianPrice");
      const elGapSummary = document.getElementById("gapReviewSummary");

      if (elGapUnits) {
        const diff = gap.unitsGap || 0;
        elGapUnits.textContent = (diff >= 0 ? `+${diff.toLocaleString()}` : `${diff.toLocaleString()}`) + " 件";
        elGapUnits.className = diff >= 0 ? "text-emerald-600 font-bold font-mono text-sm" : "text-rose-600 font-bold font-mono text-sm";
      }
      if (elGapPrice) {
        const pDiff = gap.priceDiff || 0;
        elGapPrice.textContent = (pDiff >= 0 ? `+$${pDiff.toFixed(2)}` : `-$${Math.abs(pDiff).toFixed(2)}`);
      }
      if (elGapSummary) {
        elGapSummary.textContent = gap.reviewGapSummary || "数据计算中...";
      }
    }
  }
};
