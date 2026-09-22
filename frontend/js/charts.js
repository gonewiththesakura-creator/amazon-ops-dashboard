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

  renderPriceBrackets(domId, brackets) {
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
          barMaxWidth: 32
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

  renderPriceBSR(domId, timeline, prices, bsrs) {
    const chart = this.getInstance(domId);
    if (!chart) return;

    if (!timeline || timeline.length === 0) {
      chart.clear();
      chart.setOption({
        title: {
          text: "该 ASIN 暂无历史多点位价格/BSR采样数据 (已杜绝伪造曲线)",
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
  }
};

window.addEventListener("resize", () => Charts.resizeAll());
