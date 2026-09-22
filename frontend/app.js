// ELOVNOVA Amazon Ops Dashboard - Frontend Controller

let chartInstances = {};

// Helper: Format numbers
function formatNum(num) {
  if (!num || isNaN(num)) return '0';
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return Number(num).toLocaleString();
}

function formatMoney(amount) {
  if (!amount || isNaN(amount)) return '$0';
  return '$' + Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const darkText = '#94a3b8';
const darkSplitLine = { lineStyle: { color: '#1e293b', type: 'dashed' } };
const darkAxisLine = { lineStyle: { color: '#334155' } };

function getChart(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  if (!chartInstances[id]) {
    chartInstances[id] = echarts.init(el);
  }
  return chartInstances[id];
}

// 1. Render Price & BSR Dual-Axis Line Chart
function renderPriceBsrChart(data) {
  const chart = getChart('priceBsrChart');
  if (!chart) return;

  const timeline = data.timeline || [];
  const prices = data.prices || [];
  const bsrs = data.bsrs || [];

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc', fontSize: 12 }
    },
    legend: {
      data: ['在售标价 ($)', '大类 BSR 排名走势'],
      textStyle: { color: darkText },
      top: 0
    },
    grid: { left: '3%', right: '3%', bottom: '8%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: timeline,
      axisLine: darkAxisLine,
      axisLabel: { color: darkText, fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        name: '标价 ($)',
        nameTextStyle: { color: '#f59e0b', fontSize: 11 },
        splitLine: darkSplitLine,
        axisLabel: { color: '#f59e0b', formatter: '${value}' }
      },
      {
        type: 'value',
        name: 'BSR 排名 (顶部为高排名)',
        nameTextStyle: { color: '#818cf8', fontSize: 11 },
        inverse: true, // Inverted: rank 1 at the top
        splitLine: { show: false },
        axisLabel: { color: '#818cf8', formatter: (val) => '#' + formatNum(val) }
      }
    ],
    series: [
      {
        name: '在售标价 ($)',
        type: 'line',
        data: prices,
        smooth: true,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 3 }
      },
      {
        name: '大类 BSR 排名走势',
        type: 'line',
        yAxisIndex: 1,
        data: bsrs,
        smooth: true,
        itemStyle: { color: '#6366f1' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.35)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.0)' }
          ])
        }
      }
    ]
  };
  chart.setOption(option, true);
}

// 2. Render Price Bracket Opportunities Bar + Line
function renderPriceBrackets(brackets) {
  const chart = getChart('priceBracketChart');
  if (!chart) return;

  const categories = brackets.map(b => b.bracket);
  const products = brackets.map(b => b.products);
  const unitsRatio = brackets.map(b => b.unitsRatio);

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc', fontSize: 12 }
    },
    legend: {
      data: ['在售商品数 (供给壁垒)', '销量贡献占比 (%)'],
      textStyle: { color: darkText },
      top: 0
    },
    grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: darkAxisLine,
      axisLabel: { color: darkText, fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        name: '商品数',
        nameTextStyle: { color: '#818cf8' },
        splitLine: darkSplitLine,
        axisLabel: { color: '#818cf8' }
      },
      {
        type: 'value',
        name: '销量占比 (%)',
        nameTextStyle: { color: '#f59e0b' },
        splitLine: { show: false },
        axisLabel: { color: '#f59e0b', formatter: '{value}%' }
      }
    ],
    series: [
      {
        name: '在售商品数 (供给壁垒)',
        type: 'bar',
        data: products,
        itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 35
      },
      {
        name: '销量贡献占比 (%)',
        type: 'line',
        yAxisIndex: 1,
        data: unitsRatio,
        smooth: true,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 3 }
      }
    ]
  };
  chart.setOption(option, true);
}

// 3. Render Brand Concentration Nightingale Rose Chart
function renderBrandConcentration(brandShares) {
  const chart = getChart('brandConcentrationChart');
  if (!chart) return;

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: '{b}: {c}%'
    },
    legend: {
      bottom: '0%',
      textStyle: { color: darkText, fontSize: 10 },
      itemWidth: 8,
      itemHeight: 8
    },
    series: [
      {
        name: '品牌份额',
        type: 'pie',
        radius: ['20%', '70%'],
        center: ['50%', '42%'],
        roseType: 'radius',
        itemStyle: { borderRadius: 5 },
        label: { show: false },
        data: brandShares
      }
    ]
  };
  chart.setOption(option, true);
}

// 4. Render Seller Country Distribution
function renderSellerCountry(countries) {
  const chart = getChart('sellerCountryChart');
  if (!chart) return;

  const data = countries.map(c => ({ name: c.country || '其他', value: c.share }));

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: '{b}: {c}%'
    },
    legend: { bottom: '0%', textStyle: { color: darkText, fontSize: 11 } },
    color: ['#06b6d4', '#6366f1', '#f59e0b', '#64748b'],
    series: [
      {
        type: 'pie',
        radius: '65%',
        center: ['50%', '45%'],
        data: data,
        label: { color: darkText, formatter: '{b}: {c}%' }
      }
    ]
  };
  chart.setOption(option, true);
}

// 5. Render Rating Spread Distribution
function renderRatingDist(ratings) {
  const chart = getChart('ratingDistChart');
  if (!chart) return;

  const ranges = ratings.map(r => r.ratingRange);
  const products = ratings.map(r => r.products);

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc', fontSize: 12 }
    },
    grid: { left: '3%', right: '3%', bottom: '5%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ranges,
      axisLine: darkAxisLine,
      axisLabel: { color: darkText, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: darkSplitLine,
      axisLabel: { color: darkText }
    },
    series: [
      {
        type: 'bar',
        data: products,
        itemStyle: { color: '#38bdf8', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 30
      }
    ]
  };
  chart.setOption(option, true);
}

// Render Top 100 Competitor Table
function renderCompetitorsTable(competitors) {
  const tbody = document.getElementById('competitorTableBody');
  tbody.innerHTML = '';

  if (!competitors || competitors.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-slate-500">正在调取同细分类目前100名同款竞品数据...</td></tr>';
    return;
  }

  competitors.forEach(c => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-800/40 transition';
    const bsrFormatted = c.bsr ? '#' + formatNum(c.bsr) : 'N/A';
    tr.innerHTML = `
      <td class="py-3 px-4 font-mono font-bold text-indigo-400">${c.asin}</td>
      <td class="py-3 px-4 text-white max-w-xs truncate" title="${c.title}">${c.title || '同款记忆棉/颈椎枕'}</td>
      <td class="py-3 px-4 font-medium text-slate-300">${c.brand || 'N/A'}</td>
      <td class="py-3 px-4 font-mono font-semibold text-amber-400">$${c.price || '--'}</td>
      <td class="py-3 px-4 font-mono text-indigo-300">${bsrFormatted}</td>
      <td class="py-3 px-4 font-mono text-emerald-400 font-bold">${formatNum(c.monthlyUnits)}</td>
      <td class="py-3 px-4 text-slate-300">${c.rating || '4.3'} ★ <span class="text-slate-500 text-[10px]">(${formatNum(c.ratingsCount)})</span></td>
      <td class="py-3 px-4"><a href="${c.url}" target="_blank" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-indigo-400 rounded text-[11px] font-medium transition">详情 ↗</a></td>
    `;
    tbody.appendChild(tr);
  });
}

// Render Pipeline Products (Section 3)
function renderPipelineProducts(products) {
  const container = document.getElementById('pipelineProductsContainer');
  container.innerHTML = '';

  products.forEach(p => {
    const card = document.createElement('div');
    card.className = 'p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between';
    card.innerHTML = `
      <div>
        <div class="flex items-start justify-between gap-2">
          <div>
            <h3 class="text-sm font-bold text-white">${p.name}</h3>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 mt-1 inline-block">${p.categoryLevel}</span>
          </div>
          <span class="text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">${p.decision}</span>
        </div>
        <p class="text-xs text-slate-300 mt-2.5 leading-relaxed">${p.rationale}</p>
        <div class="grid grid-cols-3 gap-2 mt-4 text-center text-xs py-2 bg-slate-800/60 rounded-xl border border-slate-700/50">
          <div>
            <div class="text-slate-400 text-[10px]">市场月估销量</div>
            <div class="text-emerald-400 font-bold font-mono mt-0.5">${formatNum(p.marketCapacityUnits)} 件</div>
          </div>
          <div>
            <div class="text-slate-400 text-[10px]">在售竞品数</div>
            <div class="text-indigo-300 font-bold font-mono mt-0.5">${p.productCount} 款</div>
          </div>
          <div>
            <div class="text-slate-400 text-[10px]">均价 / 建议价</div>
            <div class="text-amber-400 font-bold font-mono mt-0.5">$${p.avgPrice}</div>
          </div>
        </div>
      </div>
      <div class="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-indigo-300 flex items-center justify-between">
        <span>💡 选品建议: ${p.advice}</span>
        <span class="text-slate-500">状态: ${p.status}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

// Update Replenishment Calculator UI (Section 4)
function updateReplenishmentUI(data) {
  document.getElementById('resStock').textContent = `${formatNum(data.stock)} 个`;
  document.getElementById('resDailySales').textContent = `${formatNum(data.dailySales)} 个/天`;
  document.getElementById('resDays').textContent = data.stockDays;
  document.getElementById('resSeaDays').textContent = `${data.seaDays} 天 (慢但便宜)`;
  document.getElementById('resSeaRequired').textContent = `${formatNum(data.seaRequired)} 个`;
  document.getElementById('resGapDays').textContent = data.stockoutGapDays;
  document.getElementById('resAirUnits').textContent = formatNum(data.airUrgentUnits);
  document.getElementById('resGoodsCost').textContent = `${(data.goodsCost / 10000).toFixed(1)} 万元`;
  document.getElementById('resShippingCost').textContent = `${(data.totalShippingCost / 10000).toFixed(1)} 万元`;
  document.getElementById('resTotalCapital').textContent = `${(data.totalCapitalPool / 10000).toFixed(1)} 万元`;

  // Update top KPI Card for Stock Risk
  const kpiRisk = document.getElementById('kpiStockRisk');
  const kpiRiskTip = document.getElementById('kpiRiskTip');
  kpiRisk.textContent = `只够卖 ${data.stockDays} 天`;
  if (data.riskLevel === 'RED') {
    kpiRisk.className = 'kpi-value text-rose-400 font-bold';
    kpiRiskTip.textContent = '🚨 亮红灯：断货风险！';
    kpiRiskTip.className = 'kpi-sub text-rose-400 font-semibold';
  } else if (data.riskLevel === 'YELLOW') {
    kpiRisk.className = 'kpi-value text-amber-400 font-bold';
    kpiRiskTip.textContent = '⚠️ 亮黄灯：补货预警';
    kpiRiskTip.className = 'kpi-sub text-amber-400 font-semibold';
  } else {
    kpiRisk.className = 'kpi-value text-emerald-400 font-bold';
    kpiRiskTip.textContent = '✅ 绿灯：库存充足';
    kpiRiskTip.className = 'kpi-sub text-emerald-400 font-semibold';
  }
}

// Recalculate Replenishment based on inputs
async function handleRecalc() {
  const stock = parseInt(document.getElementById('inputStock').value) || 200;
  const dailySales = parseInt(document.getElementById('inputDailySales').value) || 50;
  const seaDays = parseInt(document.getElementById('inputSeaDays').value) || 30;
  const batchSize = parseInt(document.getElementById('inputBatchSize').value) || 10000;
  const unitCost = parseFloat(document.getElementById('inputUnitCost').value) || 50.0;
  const seaRate = parseFloat(document.getElementById('inputSeaRate').value) || 12.0;
  const airRate = parseFloat(document.getElementById('inputAirRate').value) || 45.0;

  try {
    const resp = await fetch('/api/replenishment/calc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stock, dailySales, seaDays, batchSize, unitCost,
        seaShippingRate: seaRate, airShippingRate: airRate
      })
    });
    const data = await resp.json();
    updateReplenishmentUI(data);
  } catch (e) {
    console.error('Failed to recalc replenishment:', e);
  }
}

// Fetch Full Dashboard Data for selected SKU
async function fetchAndRenderDashboard(marketplace, asin) {
  const loading = document.getElementById('loadingOverlay');
  loading.classList.remove('hidden');

  try {
    const resp = await fetch('/api/analyze/all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ marketplace, asin })
    });

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
    }

    const res = await resp.json();
    const asinData = res.asin || {};
    const marketData = res.market || {};

    // 1. Update Top KPI Cards (Safely format BSR!)
    document.getElementById('kpiUnits').textContent = formatNum(asinData.monthlyUnits);
    document.getElementById('kpiRevenue').textContent = formatMoney(asinData.monthlyRevenue);
    document.getElementById('kpiPrice').textContent = asinData.price ? `$${asinData.price}` : '$45.99';
    
    // Fix BSR formatting bug completely:
    let bsrText = '暂无大类BSR';
    if (typeof asinData.bsr === 'number' && asinData.bsr > 0) {
      bsrText = '#' + asinData.bsr.toLocaleString();
    } else if (typeof asinData.bsr === 'string' && asinData.bsr.indexOf('[object') === -1) {
      bsrText = '#' + asinData.bsr;
    }
    document.getElementById('kpiBsr').textContent = bsrText;
    document.getElementById('kpiCategory').textContent = asinData.nodeLabel ? asinData.nodeLabel.split('>').pop().trim() : 'Neck & Cervical';
    document.getElementById('kpiRating').textContent = `${asinData.rating || '4.2'} ★`;
    document.getElementById('kpiReviews').textContent = `${formatNum(asinData.ratingsCount)} 评价`;

    // 2. Update SKU Spec Card
    const curPreset = (res.userSkus || []).find(s => s.asin === asin) || {};
    document.getElementById('curSkuName').textContent = curPreset.name || asinData.title || 'ELOVNOVA 枕头';
    document.getElementById('curSkuAsin').textContent = `ASIN: ${asin}`;
    document.getElementById('curSkuType').textContent = curPreset.productType || asinData.nodeLabel || 'Cervical Memory Foam Pillow';
    document.getElementById('curSkuBrand').textContent = asinData.brand || 'ELOVNOVA';
    document.getElementById('curSkuParent').textContent = curPreset.parentAsin || 'B0GY2VPQPD';
    document.getElementById('curSkuNode').textContent = asinData.nodeIdPath || '3732111 (Cervical)';
    document.getElementById('curSkuPrice').textContent = `$${asinData.price || 45.99}`;
    document.getElementById('curSkuLink').href = asinData.productUrl || `https://www.amazon.com/dp/${asin}`;

    // 3. Render Charts
    renderPriceBsrChart(asinData.priceBSRChart || {});
    renderPriceBrackets(marketData.priceBrackets || []);
    renderBrandConcentration(marketData.brandSharePie || []);
    renderSellerCountry(marketData.countryDistribution || []);
    renderRatingDist(marketData.ratingDistribution || []);

    // 4. Render Competitors
    renderCompetitorsTable(asinData.topCompetitors || []);

    // 5. Render Pipeline Products & Replenishment
    renderPipelineProducts(res.pipelineProducts || []);
    if (res.replenishment) {
      updateReplenishmentUI(res.replenishment);
    }

  } catch (err) {
    console.error('Failed to load dashboard:', err);
    alert('请求失败：' + err.message);
  } finally {
    loading.classList.add('hidden');
  }
}

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('tab-active'));

  const targetTab = document.getElementById(tabId);
  const btnId = 'btnTab-' + tabId.replace('tab-', '');
  const targetBtn = document.getElementById(btnId);

  if (targetTab) targetTab.classList.remove('hidden');
  if (targetBtn) targetBtn.classList.add('tab-active');

  setTimeout(() => {
    Object.values(chartInstances).forEach(c => c && c.resize());
  }, 100);
}

// Initial binding
document.addEventListener('DOMContentLoaded', () => {
  const presetSelect = document.getElementById('skuPresetSelect');
  const marketSelect = document.getElementById('marketplaceSelect');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const recalcBtn = document.getElementById('recalcBtn');

  presetSelect.addEventListener('change', () => {
    fetchAndRenderDashboard(marketSelect.value, presetSelect.value);
  });

  marketSelect.addEventListener('change', () => {
    fetchAndRenderDashboard(marketSelect.value, presetSelect.value);
  });

  analyzeBtn.addEventListener('click', () => {
    fetchAndRenderDashboard(marketSelect.value, presetSelect.value);
  });

  if (recalcBtn) {
    recalcBtn.addEventListener('click', handleRecalc);
  }

  window.addEventListener('resize', () => {
    Object.values(chartInstances).forEach(c => c && c.resize());
  });

  // Default load first user SKU: B0GYH8WT22 (刘总枕头)
  fetchAndRenderDashboard('US', 'B0GYH8WT22');
});
