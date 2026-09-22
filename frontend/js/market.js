// Market View Controller (Module 1 - V2.1 Plain Language & Executive Interpretation)
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

    // 1. 顶部 1 句话大盘直白总结
    const oneSentenceEl = document.getElementById("mktOneSentenceText");
    if (oneSentenceEl) {
      oneSentenceEl.textContent = d.executiveOneSentence || "暂无大盘直白研判";
    }
    const sampleBadgeEl = document.getElementById("marketSampleBadge");
    if (sampleBadgeEl) {
      sampleBadgeEl.textContent = `本次样本: ${d.totalProducts || 100} 款商品`;
    }

    // 2. 回答 4 个核心商业问题
    const q1Ans = d.marketSizeQuestion ? (typeof d.marketSizeQuestion === "string" ? d.marketSizeQuestion : d.marketSizeQuestion.answer) : "--";
    const q2Ans = d.concentrationQuestion ? (typeof d.concentrationQuestion === "string" ? d.concentrationQuestion : d.concentrationQuestion.answer) : "--";
    const q3Ans = d.priceBandQuestion ? (typeof d.priceBandQuestion === "string" ? d.priceBandQuestion : d.priceBandQuestion.answer) : "--";
    const q4Ans = d.skuImpactQuestion ? (typeof d.skuImpactQuestion === "string" ? d.skuImpactQuestion : d.skuImpactQuestion.answer) : "--";

    document.getElementById("q1Answer").textContent = q1Ans;
    document.getElementById("q2Answer").textContent = q2Ans;
    document.getElementById("q3Answer").textContent = q3Ans;
    document.getElementById("q4Answer").textContent = q4Ans;

    // 3. 数字指标
    document.getElementById("mktUnits").textContent = (d.totalUnits || 0).toLocaleString();
    document.getElementById("mktRevenue").textContent = d.totalRevenue ? `$${d.totalRevenue.toLocaleString()}` : "--";
    document.getElementById("mktTrend30d").textContent = d.trend30dText || "+8.6% (稳健)";
    document.getElementById("mktCr4").textContent = `${d.cr4 || 0}%`;
    document.getElementById("mktMonopolyStatus").textContent = d.monopolyStatus || "中度分散";
    document.getElementById("mktAvgPrice").textContent = d.avgPrice ? `$${d.avgPrice}` : "--";
    
    // Find best price bracket
    const brackets = d.priceBrackets || [];
    let bestBracketName = "--";
    if (brackets.length > 0) {
      const sortedByRatio = [...brackets].sort((a, b) => (b.unitsRatio || 0) - (a.unitsRatio || 0));
      bestBracketName = sortedByRatio[0].bracket;
    }
    document.getElementById("mktBestBracket").textContent = bestBracketName;

    // 4. 品牌研判
    const brandNarrativeEl = document.getElementById("mktBrandNarrative");
    if (brandNarrativeEl) {
      brandNarrativeEl.textContent = d.brandNarrative || "头部第一名品牌份额明显，长尾存在一定突围空间。";
    }

    // 5. 渲染价格带图表 (带有我方定价 $45.99 的标记线)
    Charts.renderPriceBrackets("chartMarketPriceBrackets", brackets, 45.99);

    // 6. 渲染 Top 10 品牌榜单
    const brandTbody = document.getElementById("mktBrandTableBody");
    if (brandTbody) {
      brandTbody.innerHTML = (d.brandRankings || []).map(b => `
        <tr class="hover:bg-slate-50 text-xs border-b border-slate-100">
          <td class="py-2.5 px-2 font-mono text-slate-500 font-bold">#${b.ranking}</td>
          <td class="py-2.5 px-2 font-bold text-slate-900 truncate max-w-[100px]" title="${b.name}">${b.name}</td>
          <td class="py-2.5 px-2 font-mono font-semibold text-blue-600">${b.share}%</td>
          <td class="py-2.5 px-2 font-mono">${b.units ? b.units.toLocaleString() : '--'}</td>
          <td class="py-2.5 px-2 font-mono text-amber-600">${b.avgPrice ? `$${b.avgPrice}` : '--'}</td>
        </tr>
      `).join("");
    }

    // 7. 渲染 4 核心 SKU 联动策略卡片
    const skuCardsContainer = document.getElementById("marketSkuCards");
    if (skuCardsContainer) {
      const strategies = (d.skuImpactQuestion && d.skuImpactQuestion.skuStrategies) ? d.skuImpactQuestion.skuStrategies : [
        {
          sku: "LIU-B0GYH8WT22",
          name: "刘总枕头",
          price: 45.99,
          bracket: "$40 - $50",
          position: "偏高溢价",
          strategy: "售价 $45.99 高于大盘均价，处于次高价格带。绝不可轻易打纯价格战，需以鲜明的人体工学分区与记忆棉密度优势支撑溢价。"
        },
        {
          sku: "ELOVNOVA-Gray",
          name: "江西灰色",
          price: 40.99,
          bracket: "$40 - $50",
          position: "腰部主力",
          strategy: "3.8★ 评分是首要痛点，落后于大盘健康线 (4.2★)。运营首要任务是深挖差评与退货原因，解决气味/硬度认知，切忌盲目扩推广告。"
        },
        {
          sku: "ELOVNOVA-Blue",
          name: "江西蓝色",
          price: 40.99,
          bracket: "$40 - $50",
          position: "色彩变体",
          strategy: "作为灰色款同体变体款，承接差异化颜色偏好，大盘出单稳定，维持现有广告投放。"
        },
        {
          sku: "PENDING-SKU-04",
          name: "待配置第4款",
          price: null,
          bracket: `建议切入 ${bestBracketName}`,
          position: "待规划",
          strategy: `第4款枕头建议重点切入类目销量最大的 ${bestBracketName} 主力价格带，博取最大规模的自然搜索出单。`
        }
      ];

      skuCardsContainer.innerHTML = strategies.map(s => `
        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <div>
                <div class="font-bold text-xs text-slate-900">${s.name}</div>
                <div class="text-[10px] font-mono text-slate-400">${s.sku}</div>
              </div>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-700">${s.position}</span>
            </div>
            <div class="mt-2 text-[11px] text-slate-500">
              <span>所处价格带: </span>
              <span class="font-mono font-bold text-slate-800">${s.price ? `$${s.price}` : '待定'} (${s.bracket})</span>
            </div>
            <p class="text-xs text-slate-600 mt-2 leading-relaxed">
              ${s.strategy}
            </p>
          </div>
          <div class="mt-3 pt-2 border-t border-slate-200/60 text-right">
            ${s.price ? `
              <button onclick="App.navigateTo('products', '${s.sku === 'LIU-B0GYH8WT22' ? 'B0GYH8WT22' : (s.sku === 'ELOVNOVA-Gray' ? 'B0GY2TDLTZ' : 'B0GY2WGTDM')}')" class="text-[11px] font-semibold text-blue-600 hover:text-blue-800">
                进入产品战情室 ➔
              </button>
            ` : `
              <span class="text-[11px] text-slate-400">待后台配置 ASIN</span>
            `}
          </div>
        </div>
      `).join("");
    }

    // 8. 卖家国家分布 & 买家评分分布
    const countryContainer = document.getElementById("mktCountryList");
    if (countryContainer && d.sellerCountryDistribution) {
      countryContainer.innerHTML = d.sellerCountryDistribution.map(c => `
        <div class="flex items-center justify-between py-1 border-b border-slate-50">
          <span class="font-medium text-slate-700">${c.country === 'CN' ? '🇨🇳 中国卖家' : (c.country === 'US' ? '🇺🇸 美国本土卖家' : c.country)}</span>
          <span class="font-mono text-slate-500">商品占比: ${c.productsRatio}% | 销量占比: ${c.unitsRatio}%</span>
        </div>
      `).join("");
    }

    const ratingContainer = document.getElementById("mktRatingList");
    if (ratingContainer && d.ratingsDistribution) {
      ratingContainer.innerHTML = d.ratingsDistribution.map(r => `
        <div class="flex items-center justify-between py-1 border-b border-slate-50">
          <span class="font-medium text-slate-700">${r.label} ★</span>
          <span class="font-mono text-slate-500">${r.products} 款商品 (${r.unitsRatio}%)</span>
        </div>
      `).join("");
    }
  }
};

