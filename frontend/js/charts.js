// Light Executive Theme ECharts Helper
const Charts = {
  instances: {},

  getInstance(domId) {
    const el = document.getElementById(domId);
    if (!el) return null;
    if (!this.instances[domId]) {
      this.instances[domId] = echarts.init(el);
    }
    return this.instances[domId];
  },

  resizeAll() {
    Object.values(this.instances).forEach(inst => inst && inst.resize());
  },

  renderPriceBrackets(domId, brackets, myPrice = 45.99) {
    const chart = this.getInstance(domId);
    if (!chart) return;

    if (!brackets || brackets.length === 0) {
      chart.clear();
      chart.setOption({
        title: { text: "暂无有效价格带数据", left: "center", top: "center", textStyle: { color: "#94a3b8", fontSize: 13, fontWeight: "normal" } }
      });
      return;
    }

    const categories = brackets.map(b => b.bracket);
    const products = brackets.map(b => b.products);
    const unitsRatio = brackets.map(b => b.unitsRatio);

    // Identify which bracket myPrice falls into
    let targetBracketIndex = -1;
    if (myPrice) {
      for (let i = 0; i < brackets.length; i++) {
        const bName = brackets[i].bracket;
        // Parse numbers in "$40 - $50" or "40-50"
        const matches = bName.match(/\d+(\.\d+)?/g);
        if (matches && matches.length >= 2) {
          const low = parseFloat(matches[0]);
          const high = parseFloat(matches[1]);
          if (myPrice >= low && myPrice < high) {
            targetBracketIndex = i;
            break;
          }
        } else if (matches && matches.length === 1 && bName.includes(">")) {
          const low = parseFloat(matches[0]);
          if (myPrice >= low) {
            targetBracketIndex = i;
            break;
          }
        }
      }
    }

    const markLineData = [];
    if (targetBracketIndex >= 0 && categories[targetBracketIndex]) {
      markLineData.push({
        xAxis: categories[targetBracketIndex],
        label: {
          formatter: `我方定价 $${myPrice.toFixed(2)}`,
          position: "middle",
          color: "#dc2626",
          fontWeight: "bold",
          fontSize: 11,
          backgroundColor: "#fef2f2",
          padding: [3, 6],
          borderRadius: 4,
          borderColor: "#fecaca",
          borderWidth: 1
        },
        lineStyle: { color: "#dc2626", type: "dashed", width: 2 }
      });
    }

    chart.setOption({
      tooltip: {
        trigger: "axis",
        backgroundColor: "#ffffff",
        borderColor: "#e2e8f0",
        textStyle: { color: "#1e293b", fontSize: 12 },
        shadowBlur: 8,
        shadowColor: "rgba(0,0,0,0.06)"
      },
      legend: {
        data: ["在售商品数 (供给)", "销量占比 (%)"],
        top: 0,
        textStyle: { color: "#64748b", fontSize: 11 }
      },
      grid: { left: "3%", right: "3%", bottom: "5%", top: "16%", containLabel: true },
      xAxis: {
        type: "category",
        data: categories,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 11 }
      },
      yAxis: [
        {
          type: "value",
          name: "商品数",
          nameTextStyle: { color: "#64748b", fontSize: 11 },
          splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
          axisLabel: { color: "#64748b" }
        },
        {
          type: "value",
          name: "销量占比 %",
          nameTextStyle: { color: "#2563eb", fontSize: 11 },
          splitLine: { show: false },
          axisLabel: { color: "#2563eb", formatter: "{value}%" }
        }
      ],
      series: [
        {
          name: "在售商品数 (供给)",
          type: "bar",
          data: products,
          itemStyle: { color: "#cbd5e1", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 32,
          markLine: markLineData.length > 0 ? {
            symbol: ["none", "none"],
            data: markLineData
          } : undefined
        },
        {
          name: "销量占比 (%)",
          type: "line",
          yAxisIndex: 1,
          data: unitsRatio,
          smooth: true,
          itemStyle: { color: "#2563eb" },
          lineStyle: { width: 3 }
        }
      ]
    }, true);
  },

  renderPriceStepChart(domId, priceStepPoints, meta = {}) {
    const chart = this.getInstance(domId);
    if (!chart) return;

    if (!priceStepPoints || priceStepPoints.length === 0) {
      chart.clear();
      chart.setOption({
        title: {
          text: meta.lastPriceChange || "暂无历史调价记录（标价保持稳定）",
          subtext: "基于真实 Keepa 价格采集，严禁生成伪造价格走势",
          left: "center",
          top: "center",
          textStyle: { color: "#475569", fontSize: 13, fontWeight: "bold" },
          subtextStyle: { color: "#94a3b8", fontSize: 11 }
        }
      });
      return;
    }

    const dates = priceStepPoints.map(p => p.date);
    const prices = priceStepPoints.map(p => p.price);

    const isConstant = meta.hasPriceChanged === false || (new Set(prices)).size <= 1;

    chart.setOption({
      title: isConstant ? {
        text: `标价持续稳定在 $${prices[0]} (无调价历史)`,
        left: "center",
        top: 6,
        textStyle: { color: "#059669", fontSize: 12, fontWeight: "bold" }
      } : undefined,
      tooltip: {
        trigger: "axis",
        backgroundColor: "#ffffff",
        borderColor: "#e2e8f0",
        textStyle: { color: "#1e293b", fontSize: 12 },
        formatter: (params) => {
          if (!params || !params.length) return "";
          const p = params[0];
          return `<div class="font-sans">
            <div class="text-xs text-slate-500">${p.name}</div>
            <div class="text-sm font-bold text-amber-600 mt-1">标价: $${p.value}</div>
          </div>`;
        }
      },
      grid: { left: "4%", right: "4%", bottom: "8%", top: isConstant ? "22%" : "12%", containLabel: true },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 10 }
      },
      yAxis: {
        type: "value",
        name: "标价 ($)",
        nameTextStyle: { color: "#d97706", fontSize: 11 },
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#d97706", formatter: "${value}" },
        min: (value) => Math.max(0, Math.floor(value.min - 5)),
        max: (value) => Math.ceil(value.max + 5)
      },
      series: [
        {
          name: "历史标价",
          type: "line",
          step: "end",
          data: prices,
          itemStyle: { color: "#d97706" },
          lineStyle: { width: 2.5, color: "#d97706" },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(217, 119, 6, 0.15)" },
              { offset: 1, color: "rgba(217, 119, 6, 0.0)" }
            ])
          },
          markPoint: isConstant ? undefined : {
            data: [
              { type: "max", name: "最高价" },
              { type: "min", name: "最低价" }
            ]
          }
        }
      ]
    }, true);
  },

  renderSalesBsrChart(domId, bsrPoints = [], salesPoints = []) {
    const chart = this.getInstance(domId);
    if (!chart) return;

    if ((!bsrPoints || bsrPoints.length === 0) && (!salesPoints || salesPoints.length === 0)) {
      chart.clear();
      chart.setOption({
        title: {
          text: "暂无历史采样点位 (系统坚守零伪造原则)",
          subtext: "每天 08:30 自动抓取并记录新数据点位",
          left: "center",
          top: "center",
          textStyle: { color: "#94a3b8", fontSize: 12, fontWeight: "normal" },
          subtextStyle: { color: "#cbd5e1", fontSize: 11 }
        }
      });
      return;
    }

    // Merge dates
    const dateSet = new Set();
    (bsrPoints || []).forEach(p => dateSet.add(p.date));
    (salesPoints || []).forEach(p => dateSet.add(p.date));
    const dates = Array.from(dateSet).sort();

    const bsrMap = {};
    (bsrPoints || []).forEach(p => { bsrMap[p.date] = p.bsr; });
    const bsrData = dates.map(d => bsrMap[d] !== undefined ? bsrMap[d] : null);

    chart.setOption({
      tooltip: {
        trigger: "axis",
        backgroundColor: "#ffffff",
        borderColor: "#e2e8f0",
        textStyle: { color: "#1e293b", fontSize: 12 },
        formatter: (params) => {
          if (!params || !params.length) return "";
          let html = `<div class="font-sans"><div class="text-xs text-slate-500">${params[0].name}</div>`;
          params.forEach(p => {
            if (p.value !== null && p.value !== undefined) {
              html += `<div class="text-xs font-semibold mt-1" style="color:${p.color}">${p.seriesName}: #${Number(p.value).toLocaleString()}</div>`;
            }
          });
          html += `</div>`;
          return html;
        }
      },
      legend: {
        data: ["大类 BSR 排名"],
        top: 0,
        textStyle: { color: "#64748b", fontSize: 11 }
      },
      grid: { left: "4%", right: "4%", bottom: "8%", top: "14%", containLabel: true },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 10 }
      },
      yAxis: {
        type: "value",
        name: "BSR (顶端为高排名)",
        nameTextStyle: { color: "#2563eb", fontSize: 11 },
        inverse: true,
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#2563eb", formatter: "#{value}" }
      },
      series: [
        {
          name: "大类 BSR 排名",
          type: "line",
          data: bsrData,
          smooth: true,
          itemStyle: { color: "#2563eb" },
          lineStyle: { width: 2.5, color: "#2563eb" },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(37, 99, 235, 0.15)" },
              { offset: 1, color: "rgba(37, 99, 235, 0.0)" }
            ])
          }
        }
      ]
    }, true);
  },

  renderPriceBSR(domId, timeline, prices, bsrs) {
    const chart = this.getInstance(domId);
    if (!chart) return;

    if (!timeline || timeline.length === 0) {
      chart.clear();
      chart.setOption({
        title: {
          text: "该 ASIN 暂无历史采样数据 (已杜绝伪造曲线)",
          left: "center",
          top: "center",
          textStyle: { color: "#94a3b8", fontSize: 12, fontWeight: "normal" }
        }
      });
      return;
    }

    chart.setOption({
      tooltip: {
        trigger: "axis",
        backgroundColor: "#ffffff",
        borderColor: "#e2e8f0",
        textStyle: { color: "#1e293b", fontSize: 12 }
      },
      legend: {
        data: ["标价 ($)", "大类 BSR 排名"],
        top: 0,
        textStyle: { color: "#64748b", fontSize: 11 }
      },
      grid: { left: "3%", right: "3%", bottom: "5%", top: "16%", containLabel: true },
      xAxis: {
        type: "category",
        data: timeline,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 11 }
      },
      yAxis: [
        {
          type: "value",
          name: "标价 ($)",
          nameTextStyle: { color: "#d97706" },
          splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
          axisLabel: { color: "#d97706", formatter: "${value}" }
        },
        {
          type: "value",
          name: "BSR (顶端为高排名)",
          nameTextStyle: { color: "#2563eb" },
          inverse: true,
          splitLine: { show: false },
          axisLabel: { color: "#2563eb", formatter: "#{value}" }
        }
      ],
      series: [
        {
          name: "标价 ($)",
          type: "line",
          data: prices,
          smooth: true,
          itemStyle: { color: "#f59e0b" },
          lineStyle: { width: 2.5 }
        },
        {
          name: "大类 BSR 排名",
          type: "line",
          yAxisIndex: 1,
          data: bsrs,
          smooth: true,
          itemStyle: { color: "#2563eb" },
          lineStyle: { width: 2.5 }
        }
      ]
    }, true);
  },

  renderMarket12mTrend(domId, monthlyPoints, metric = "units") {
    const chart = this.getInstance(domId);
    if (!chart) return;
    if (!monthlyPoints || monthlyPoints.length === 0) {
      chart.clear();
      chart.setOption({
        title: { text: "历史数据积累中 (暂无完整12个月时序)", left: "center", top: "center", textStyle: { color: "#94a3b8", fontSize: 13 } }
      });
      return;
    }

    const months = monthlyPoints.map(p => p.month);
    const isUnits = metric === "units";
    const dataValues = monthlyPoints.map(p => isUnits ? p.units : p.revenue);
    const metricName = isUnits ? "大盘月销量 (件)" : "大盘销售额 ($)";
    const color = isUnits ? "#2563eb" : "#059669";
    const areaColor = isUnits ? "rgba(37, 99, 235, 0.12)" : "rgba(5, 150, 105, 0.12)";

    chart.setOption({
      tooltip: {
        trigger: "axis",
        formatter: (params) => {
          const pt = params[0];
          const raw = monthlyPoints[pt.dataIndex];
          const valStr = isUnits ? `${pt.value.toLocaleString()} 件` : `$${pt.value.toLocaleString()}`;
          return `<div class="font-bold text-xs text-slate-800">${pt.name}</div>
                  <div class="text-xs text-slate-600 mt-1">${metricName}: <span class="font-bold text-blue-600">${valStr}</span></div>
                  <div class="text-[11px] text-slate-400 mt-0.5">均价: $${raw.avgPrice?.toFixed(1) || '--'}</div>`;
        }
      },
      grid: { left: "3%", right: "3%", bottom: "6%", top: "12%", containLabel: true },
      xAxis: {
        type: "category",
        data: months,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 11 }
      },
      yAxis: {
        type: "value",
        name: isUnits ? "月销量 (件)" : "月销售额 ($)",
        nameTextStyle: { color: "#64748b", fontSize: 11 },
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: {
          color: "#64748b",
          formatter: (v) => isUnits ? `${(v / 10000).toFixed(0)}w` : `$${(v / 10000).toFixed(0)}w`
        }
      },
      series: [
        {
          name: metricName,
          type: "line",
          data: dataValues,
          smooth: 0.35,
          itemStyle: { color: color },
          lineStyle: { width: 3, color: color },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: areaColor },
              { offset: 1, color: "rgba(255, 255, 255, 0.0)" }
            ])
          },
          markPoint: {
            data: [
              { type: "max", name: "旺季峰值" }
            ],
            label: { fontSize: 10 }
          }
        }
      ]
    }, true);
  },

  renderSku90dTrends(domId, skuTrendData, metric = "units") {
    const chart = this.getInstance(domId);
    if (!chart) return;
    if (!skuTrendData || !skuTrendData.dates || skuTrendData.dates.length === 0) {
      chart.clear();
      chart.setOption({
        title: { text: "时序数据积累中...", left: "center", top: "center", textStyle: { color: "#94a3b8", fontSize: 13 } }
      });
      return;
    }

    const dates = skuTrendData.dates;
    const seriesObj = skuTrendData.series || {};
    const configuredKeys = Object.keys(seriesObj).filter(k => seriesObj[k].isConfigured && seriesObj[k][metric]);

    const colors = ["#2563eb", "#059669", "#d97706", "#9333ea"];
    const seriesList = configuredKeys.map((k, idx) => {
      const item = seriesObj[k];
      return {
        name: item.name.split(" ")[0],
        type: "line",
        data: item[metric],
        smooth: true,
        itemStyle: { color: colors[idx % colors.length] },
        lineStyle: { width: 2.5 }
      };
    });

    const isBsr = metric === "bsr";

    chart.setOption({
      tooltip: {
        trigger: "axis",
        backgroundColor: "#ffffff",
        borderColor: "#e2e8f0",
        shadowBlur: 8,
        shadowColor: "rgba(0,0,0,0.06)"
      },
      legend: {
        top: 0,
        textStyle: { color: "#64748b", fontSize: 11 }
      },
      grid: { left: "3%", right: "3%", bottom: "6%", top: "16%", containLabel: true },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 11 }
      },
      yAxis: {
        type: "value",
        name: metric === "units" ? "月销量 (件)" : (metric === "price" ? "标价 ($)" : "大类 BSR 排名"),
        inverse: isBsr,
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: {
          color: "#64748b",
          formatter: (v) => isBsr ? `#${v}` : (metric === "price" ? `$${v}` : v)
        }
      },
      series: seriesList
    }, true);
  },

  renderCompetitorHorizontalBar(domId, compList) {
    const chart = this.getInstance(domId);
    if (!chart) return;
    if (!compList || compList.length === 0) {
      chart.clear();
      chart.setOption({
        title: { text: "暂无直接竞品对标数据", left: "center", top: "center", textStyle: { color: "#94a3b8", fontSize: 13 } }
      });
      return;
    }

    // Sort ascending so highest appears on top
    const sorted = [...compList].sort((a, b) => a.monthlyUnits - b.monthlyUnits);
    const names = sorted.map(c => c.brand || c.asin);
    const units = sorted.map(c => c.monthlyUnits);

    chart.setOption({
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const pt = params[0];
          const raw = sorted[pt.dataIndex];
          const isOur = raw.isOur ? '<span class="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-bold">我方产品</span>' : '<span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px]">直接竞品</span>';
          return `<div class="font-bold text-xs">${raw.brand} ${isOur}</div>
                  <div class="text-xs text-slate-600 mt-1">ASIN: <span class="font-mono text-slate-800">${raw.asin}</span></div>
                  <div class="text-xs text-slate-600 mt-0.5">月销量: <b class="text-blue-600">${raw.monthlyUnits.toLocaleString()} 件</b></div>
                  <div class="text-xs text-slate-600 mt-0.5">定价: $${raw.price || '--'} | 评分: ${raw.rating || '--'}⭐ (${raw.reviews?.toLocaleString() || 0} reviews)</div>`;
        }
      },
      grid: { left: "4%", right: "8%", bottom: "4%", top: "4%", containLabel: true },
      xAxis: {
        type: "value",
        name: "月销量 (件)",
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#64748b", formatter: (v) => `${(v / 1000).toFixed(0)}k` }
      },
      yAxis: {
        type: "category",
        data: names,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#334155", fontSize: 11, fontWeight: "500" }
      },
      series: [
        {
          name: "月销量",
          type: "bar",
          data: units.map((val, idx) => {
            const raw = sorted[idx];
            return {
              value: val,
              itemStyle: {
                color: raw.isOur ? "#2563eb" : "#94a3b8",
                borderRadius: [0, 4, 4, 0]
              }
            };
          }),
          barMaxWidth: 24,
          label: {
            show: true,
            position: "right",
            formatter: (p) => `${p.value.toLocaleString()}`,
            color: "#475569",
            fontSize: 11
          }
        }
      ]
    }, true);
  },

  renderCategory12mCurve(domId, trendPoints) {
    const chart = this.getInstance(domId);
    if (!chart) return;
    if (!trendPoints || trendPoints.length === 0) return;

    const months = trendPoints.map(p => p.month);
    const units = trendPoints.map(p => p.units);

    chart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "3%", bottom: "6%", top: "10%", containLabel: true },
      xAxis: {
        type: "category",
        data: months,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#64748b", fontSize: 10 }
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#64748b", formatter: (v) => `${(v / 1000).toFixed(0)}k` }
      },
      series: [
        {
          type: "line",
          data: units,
          smooth: true,
          itemStyle: { color: "#059669" },
          lineStyle: { width: 2.5 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(5, 150, 105, 0.15)" },
              { offset: 1, color: "rgba(255, 255, 255, 0)" }
            ])
          }
        }
      ]
    }, true);
  },

  renderKeywordsBar(domId, keywordsList) {
    const chart = this.getInstance(domId);
    if (!chart) return;
    if (!keywordsList || keywordsList.length === 0) {
      chart.clear();
      chart.setOption({
        title: { text: "暂无关键词搜索数据", left: "center", top: "center", textStyle: { color: "#94a3b8", fontSize: 12 } }
      });
      return;
    }

    const words = keywordsList.map(k => k.keyword);
    const searches = keywordsList.map(k => typeof k.searches === "number" ? k.searches : 0);

    chart.setOption({
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { left: "3%", right: "3%", bottom: "16%", top: "10%", containLabel: true },
      xAxis: {
        type: "category",
        data: words,
        axisLabel: { color: "#64748b", fontSize: 10, interval: 0, rotate: 20 }
      },
      yAxis: {
        type: "value",
        name: "月搜索量",
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#64748b" }
      },
      series: [
        {
          type: "bar",
          data: searches,
          itemStyle: { color: "#3b82f6", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 30
        }
      ]
    }, true);
  },

  renderBroadSplitComparison(domId, subDirections) {
    const chart = this.getInstance(domId);
    if (!chart) return;
    if (!subDirections || subDirections.length === 0) return;

    const names = subDirections.map(s => s.name.split(" ")[0]);
    const searches = subDirections.map(s => s.estimatedMonthlySearches);

    chart.setOption({
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const pt = params[0];
          const raw = subDirections[pt.dataIndex];
          return `<div class="font-bold text-xs">${raw.name}</div>
                  <div class="text-xs text-slate-600 mt-1">核心词: <span class="font-mono text-blue-600">${raw.keyword}</span></div>
                  <div class="text-xs text-slate-600 mt-0.5">月搜索: <b>${raw.estimatedMonthlySearches.toLocaleString()} 次</b></div>
                  <div class="text-xs text-slate-600 mt-0.5">受众: ${raw.audience} | 价格: ${raw.priceTier}</div>
                  <div class="text-xs text-emerald-600 font-semibold mt-0.5">信号: ${raw.demandSignal}</div>`;
        }
      },
      grid: { left: "4%", right: "6%", bottom: "8%", top: "12%", containLabel: true },
      xAxis: {
        type: "category",
        data: names,
        axisLine: { lineStyle: { color: "#cbd5e1" } },
        axisLabel: { color: "#475569", fontSize: 11, interval: 0 }
      },
      yAxis: {
        type: "value",
        name: "细分月搜容量",
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#64748b", formatter: (v) => `${(v / 1000).toFixed(0)}k` }
      },
      series: [
        {
          name: "月搜索量",
          type: "bar",
          data: searches,
          itemStyle: { color: "#f59e0b", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 36,
          label: {
            show: true,
            position: "top",
            formatter: (p) => `${(p.value / 1000).toFixed(0)}k`,
            color: "#64748b",
            fontSize: 10
          }
        }
      ]
    }, true);
  }
};

window.addEventListener("resize", () => Charts.resizeAll());
