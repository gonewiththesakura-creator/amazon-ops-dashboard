// Opportunity Lab (New Categories) Controller (Module 4 - V2.4 & V2.5)
const OpportunityView = {
  async init() {
    await this.loadProjects();
    this.bindEvents();
  },

  bindEvents() {
    const btn = document.getElementById("btnStartResearch");
    const input = document.getElementById("inputResearchQuery");

    if (btn && input) {
      btn.onclick = async () => {
        const q = input.value.trim();
        if (!q) {
          alert("请输入您想调研的新赛道想法（例如：shoes、铅笔、防驼背坐垫、宠物慢食碗）");
          return;
        }

        btn.disabled = true;
        btn.innerHTML = `<span class="animate-spin mr-1">↻</span> 正在执行多路 MCP 查询与宽词拆解...`;

        const res = await API.conductResearch(q);
        btn.disabled = false;
        btn.innerHTML = `启动 AI 自动化调研`;

        if (res && res.status === "ok") {
          input.value = "";
          await this.loadProjects();
          alert("新赛道调研完成，图表与分析已入库！");
        } else {
          alert("调研请求失败：" + (res?.error || "未知异常"));
        }
      };
    }
  },

  async loadProjects() {
    const res = await API.getResearchProjects();
    if (!res || res.status !== "ok" || !res.data) return;

    const container = document.getElementById("researchProjectsContainer");
    if (!container) return;

    const projects = res.data || [];
    if (projects.length === 0) {
      container.innerHTML = `
        <div class="exec-card p-10 text-center text-slate-400 text-xs">
          <div class="text-2xl mb-2">🧪</div>
          <div>暂无新赛道调研项目。在上方输入您的产品构想（如 "shoes"、"铅笔"、"防驼背坐垫"）即可开启多路真实调研。</div>
        </div>
      `;
      return;
    }

    container.innerHTML = projects.map(p => {
      const plan = p.plan || {};
      const findings = p.findings || {};
      const why = findings.why || [];
      const opps = findings.opportunities || [];
      const actions = findings.nextActions || [];
      const warning = findings.complianceWarning || "";
      const decStatus = findings.decisionStatus || p.status || "调研完成";
      const isBroad = Boolean(findings.isBroad);
      const dataState = findings.dataState || "valid";
      const totalSearches = findings.totalSearches;

      let badgeColor = "bg-blue-100 text-blue-800 border-blue-200";
      if (decStatus.includes("值得深入")) badgeColor = "bg-emerald-100 text-emerald-800 border-emerald-200";
      else if (decStatus.includes("宽词拆解") || decStatus.includes("有信号")) badgeColor = "bg-amber-100 text-amber-800 border-amber-200";
      else if (decStatus.includes("暂未取得") || decStatus.includes("数据不足")) badgeColor = "bg-sky-100 text-sky-800 border-sky-200";
      else if (decStatus.includes("零搜索") || decStatus.includes("暂不建议")) badgeColor = "bg-rose-100 text-rose-800 border-rose-200";

      // P0 Semantic Search Display (no_data != 0)
      let searchesDisplay = "";
      if (dataState === "broad_split") {
        searchesDisplay = `<span class="text-amber-600 font-bold">5大细分方向共 ${(totalSearches || 0).toLocaleString()} 次/月</span>`;
      } else if (dataState === "valid") {
        searchesDisplay = `<span class="font-bold text-slate-800">${(totalSearches || 0).toLocaleString()} 次/月</span>`;
      } else if (dataState === "explicit_zero") {
        searchesDisplay = `<span class="text-rose-600 font-bold">明确为 0 次搜索 (伪需求)</span>`;
      } else {
        searchesDisplay = `<span class="text-blue-600 font-bold">暂未取得搜索数据 (非0)</span>`;
      }

      const chartId = `researchChart_${p.id}`;

      // Broad Split UI vs Single Category UI
      let visualContent = "";
      if (isBroad && findings.subDirections) {
        visualContent = `
          <div class="mt-4 p-4 rounded-xl bg-amber-50/50 border border-amber-200/80 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-900">🔍 宽泛大词 5 维细分子赛道拆解矩阵</span>
              <span class="text-[11px] text-amber-700">避免大牌正面垄断，建议选 1 个垂直切入</span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-5 gap-2.5">
              ${findings.subDirections.map((sd, sidx) => `
                <div class="p-3 bg-white rounded-lg border border-amber-200/80 shadow-xs flex flex-col justify-between space-y-2">
                  <div>
                    <div class="text-[10px] font-bold text-amber-600 uppercase tracking-wider">方向 ${sidx + 1}</div>
                    <div class="text-xs font-bold text-slate-900 mt-0.5 leading-snug">${sd.name}</div>
                    <div class="text-[11px] font-mono text-blue-600 mt-1">${sd.keyword}</div>
                    <div class="text-[10px] text-slate-500 mt-1">受众: ${sd.audience}</div>
                  </div>
                  <div class="pt-2 border-t border-slate-100 text-[11px]">
                    <div class="text-slate-700">月搜: <b class="text-slate-900">${sd.estimatedMonthlySearches.toLocaleString()}</b></div>
                    <div class="text-slate-700">定价: <b class="text-emerald-600">${sd.priceTier}</b></div>
                    <div class="text-[10px] text-emerald-700 font-semibold mt-0.5">${sd.demandSignal}</div>
                  </div>
                </div>
              `).join("")}
            </div>

            <!-- Comparison Bar Chart -->
            <div class="bg-white p-3 rounded-lg border border-amber-200 mt-3">
              <div class="text-xs font-bold text-slate-800 mb-1">5 大细分方向月搜索容量对比图</div>
              <div id="${chartId}" style="height: 180px; width: 100%;"></div>
            </div>
          </div>
        `;
      } else {
        visualContent = `
          <!-- Charts Section for Single Category -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div class="bg-white p-3 rounded-lg border border-slate-200">
              <div class="text-xs font-bold text-slate-800 mb-1">核心关键词搜索需求对比 (Top 10)</div>
              <div id="${chartId}_kw" style="height: 180px; width: 100%;"></div>
            </div>
            <div class="bg-white p-3 rounded-lg border border-slate-200">
              <div class="text-xs font-bold text-slate-800 mb-1">主流价格带分布统计</div>
              <div id="${chartId}_price" style="height: 180px; width: 100%;"></div>
            </div>
          </div>
        `;
      }

      return `
        <div class="exec-card p-5 mb-5 space-y-4">
          <!-- 标题与结论评级徽章 -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-sm font-bold text-slate-900">${p.title}</h3>
                <span class="text-[11px] font-mono px-2 py-0.5 rounded border ${badgeColor} font-bold">
                  ${decStatus}
                </span>
              </div>
              <p class="text-xs text-slate-500 mt-0.5">老板提问: "${p.user_question || '--'}"</p>
            </div>
            <div class="text-xs text-slate-500 font-mono">
              需求状态: ${searchesDisplay}
            </div>
          </div>

          <!-- 老板模式核心卡：结论 + 为什么 + 下一步 -->
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-3">
            <div>
              <span class="font-bold text-slate-900 block mb-1">📌 商业结论：</span>
              <p class="text-slate-700 leading-relaxed font-medium bg-white p-2.5 rounded border border-slate-200">
                ${findings.conclusion || '数据采集与分析已完成。'}
              </p>
            </div>

            <!-- 为什么得出的结论 -->
            ${why.length > 0 ? `
              <div>
                <span class="font-bold text-slate-800 block mb-1">💡 为什么得出该结论 (4大维度证据)：</span>
                <ul class="space-y-1 pl-1">
                  ${why.map(w => `<li class="text-slate-600 flex items-start gap-1.5"><span class="text-blue-500">•</span><span>${w}</span></li>`).join("")}
                </ul>
              </div>
            ` : ''}

            <!-- 商业机会 -->
            ${opps.length > 0 ? `
              <div>
                <span class="font-bold text-emerald-800 block mb-1">🚀 识别到的潜在商业机会：</span>
                <ul class="space-y-1 pl-1">
                  ${opps.map(o => `<li class="text-emerald-700 flex items-start gap-1.5 font-medium"><span class="text-emerald-500">✓</span><span>${o}</span></li>`).join("")}
                </ul>
              </div>
            ` : ''}

            <!-- 老板下一步行动建议 -->
            ${actions.length > 0 ? `
              <div class="p-3 bg-blue-50/60 rounded-lg border border-blue-200 text-blue-950">
                <span class="font-bold block mb-1">🎯 建议老板下一步动作 (Actionable Next Steps)：</span>
                <ul class="space-y-1">
                  ${actions.map(a => `<li class="text-slate-700 flex items-start gap-1.5"><span>→</span><span>${a}</span></li>`).join("")}
                </ul>
              </div>
            ` : ''}
          </div>

          <!-- 图表渲染区域 -->
          ${visualContent}

          <!-- 合规警示与证据链 -->
          <div class="p-3 bg-amber-50/60 rounded-lg border border-amber-200 text-[11px] text-amber-900">
            <span class="font-bold">⚠️ 合规与认证警示：</span>
            <span>${warning || '普通消费品标准，建议在批量备货前进行外观专利防侵权排查。'}</span>
          </div>
        </div>
      `;
    }).join("");

    // Render charts for each project card
    setTimeout(() => {
      projects.forEach(p => {
        const findings = p.findings || {};
        if (findings.isBroad && findings.subDirections) {
          Charts.renderBroadSplitComparison(`researchChart_${p.id}`, findings.subDirections);
        } else {
          if (findings.keywordsBarChart) {
            Charts.renderKeywordsBar(`researchChart_${p.id}_kw`, findings.keywordsBarChart);
          }
          if (findings.priceDistributionChart) {
            const chart = Charts.getInstance(`researchChart_${p.id}_price`);
            if (chart) {
              const brackets = findings.priceDistributionChart;
              chart.setOption({
                tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
                grid: { left: "3%", right: "3%", bottom: "8%", top: "10%", containLabel: true },
                xAxis: { type: "category", data: brackets.map(b => b.bracket), axisLabel: { color: "#64748b", fontSize: 10 } },
                yAxis: { type: "value", splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } } },
                series: [{ type: "bar", data: brackets.map(b => b.count), itemStyle: { color: "#10b981", borderRadius: [4, 4, 0, 0] }, barMaxWidth: 28 }]
              }, true);
            }
          }
        }
      });
    }, 100);
  }
};
