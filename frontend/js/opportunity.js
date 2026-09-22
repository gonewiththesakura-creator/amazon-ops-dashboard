// Opportunity Lab (New Categories) Controller (Module 4)
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
          alert("请输入您想调研的新赛道想法（例如：小学一年级开学用品组合、露营车载充气床）");
          return;
        }

        btn.disabled = true;
        btn.innerHTML = `<span class="animate-spin mr-1">↻</span> 正在调用 MCP 拆解类目与测算中...`;

        const res = await API.conductResearch(q);
        btn.disabled = false;
        btn.innerHTML = `启动 AI 自动化调研`;

        if (res && res.status === "ok") {
          input.value = "";
          await this.loadProjects();
          alert("新赛道调研完成，已入库！");
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
          <div>暂无新赛道调研项目。在上方输入您的产品构想即可开启 4 维度严肃评估。</div>
        </div>
      `;
      return;
    }

    container.innerHTML = projects.map(p => {
      const plan = p.plan || {};
      const findings = p.findings || {};
      const levels = plan.categoryLevels || [];
      const why = findings.why || [];
      const opps = findings.opportunities || [];
      const actions = findings.nextActions || [];
      const keywords = findings.discoveredKeywords || [];
      const evidence = findings.evidenceChain || [];
      const warning = findings.complianceWarning || "";
      const decStatus = findings.decisionStatus || p.status || "调研完成";
      const totalSearches = findings.totalSearches || 0;

      let badgeColor = "bg-blue-100 text-blue-800 border-blue-200";
      if (decStatus.includes("值得深入")) badgeColor = "bg-emerald-100 text-emerald-800 border-emerald-200";
      else if (decStatus.includes("有信号")) badgeColor = "bg-amber-100 text-amber-800 border-amber-200";
      else if (decStatus.includes("数据不足")) badgeColor = "bg-sky-100 text-sky-800 border-sky-200";
      else if (decStatus.includes("暂不建议")) badgeColor = "bg-rose-100 text-rose-800 border-rose-200";

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
              <p class="text-xs text-slate-500 mt-0.5">老板原提问: "${p.user_question || '--'}"</p>
            </div>
            <div class="text-xs text-slate-400 font-mono">
              月搜索量: <span class="font-bold text-slate-800">${totalSearches.toLocaleString()}</span> 次
            </div>
          </div>

          <!-- 老板模式核心卡：结论 + 为什么 + 下一步 -->
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-3">
            <!-- 核心结论 -->
            <div>
              <span class="font-bold text-slate-900 block mb-1">📌 严肃商业结论：</span>
              <p class="text-slate-700 leading-relaxed font-medium bg-white p-2.5 rounded border border-slate-200">
                ${findings.conclusion || '数据采集与分析已完成。'}
              </p>
            </div>

            <!-- 为什么 (判断依据) -->
            ${why.length > 0 ? `
              <div>
                <span class="font-bold text-slate-900 block mb-1">🔍 为什么这么判断：</span>
                <ul class="space-y-1 text-slate-600 leading-relaxed bg-white p-2.5 rounded border border-slate-200">
                  ${why.map(w => `<li>• ${w}</li>`).join("")}
                </ul>
              </div>
            ` : ''}

            <!-- 核心机会点 (若有) -->
            ${opps.length > 0 ? `
              <div class="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200/60">
                <span class="font-bold text-emerald-800 block mb-1">✓ 捕捉到的机会点：</span>
                <ul class="space-y-1 text-slate-700 leading-relaxed">
                  ${opps.map(o => `<li>• ${o}</li>`).join("")}
                </ul>
              </div>
            ` : ''}

            <!-- 合规与类目政策警示 -->
            ${warning ? `
              <div class="p-3 rounded-lg bg-rose-50/80 border border-rose-200 text-rose-900">
                <div class="font-bold flex items-center gap-1.5 mb-1 text-rose-800">
                  <span>🚨</span>
                  <span>亚马逊合规与类目准入警示：</span>
                </div>
                <div class="text-[11px] leading-relaxed text-rose-700 font-medium">
                  ${warning}
                </div>
              </div>
            ` : ''}

            <!-- 建议直接行动 -->
            ${actions.length > 0 ? `
              <div class="p-3 rounded-lg bg-blue-50/60 border border-blue-200 text-slate-700">
                <span class="font-bold text-blue-900 block mb-1">🎯 建议下一步落地动作：</span>
                <div class="space-y-1 text-slate-700">
                  ${actions.map(act => `<div>${act}</div>`).join("")}
                </div>
              </div>
            ` : ''}
          </div>

          <!-- 折叠详细数据与调研证据 -->
          <details class="text-xs text-slate-500 pt-1">
            <summary class="cursor-pointer font-bold text-blue-600 hover:text-blue-800">
              📊 查看详细数据与调研证据（核心搜索词列表 / 类目层级 / 证据链）▾
            </summary>
            <div class="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-3">
              <!-- 探测类目层级 -->
              ${levels.length > 0 ? `
                <div>
                  <span class="font-bold text-slate-700 block mb-1">探测类目层级：</span>
                  <div class="flex flex-wrap items-center gap-1 font-mono text-[11px]">
                    ${levels.map((lvl, idx) => `
                      <span class="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-800">${lvl}</span>
                      ${idx < levels.length - 1 ? '<span class="text-slate-400">➔</span>' : ''}
                    `).join("")}
                  </div>
                </div>
              ` : ''}

              <!-- 搜索词明细表 -->
              ${keywords.length > 0 ? `
                <div>
                  <span class="font-bold text-slate-700 block mb-1">关键词挖掘与月搜索量样本：</span>
                  <div class="overflow-x-auto">
                    <table class="w-full text-left text-[11px] bg-white rounded border border-slate-200">
                      <thead class="bg-slate-100 text-slate-600 border-b border-slate-200 font-semibold">
                        <tr>
                          <th class="py-1.5 px-2">关键词 (Keyword)</th>
                          <th class="py-1.5 px-2">月搜索量 (Searches)</th>
                          <th class="py-1.5 px-2">均价 (Avg Price)</th>
                          <th class="py-1.5 px-2">供需比 (SPR)</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${keywords.map(kw => `
                          <tr class="border-b border-slate-100">
                            <td class="py-1.5 px-2 font-mono font-medium text-slate-800">${kw.keyword || '--'}</td>
                            <td class="py-1.5 px-2 font-mono">${kw.searches ? Number(kw.searches).toLocaleString() : 0}</td>
                            <td class="py-1.5 px-2 font-mono">${kw.avgPrice ? `$${kw.avgPrice}` : '--'}</td>
                            <td class="py-1.5 px-2 font-mono">${kw.spr || '--'}</td>
                          </tr>
                        `).join("")}
                      </tbody>
                    </table>
                  </div>
                </div>
              ` : ''}

              <!-- 证据链 -->
              ${evidence.length > 0 ? `
                <div>
                  <span class="font-bold text-slate-700 block mb-1">完整证据链记录：</span>
                  <div class="space-y-0.5 text-[11px] font-mono text-slate-600 bg-white p-2 rounded border border-slate-200">
                    ${evidence.map(ev => `<div>• ${ev}</div>`).join("")}
                  </div>
                </div>
              ` : ''}
            </div>
          </details>

          <div class="text-[10px] text-slate-400 text-right pt-1 border-t border-slate-100">
            调研归档时间: ${p.created_at || '--'} | 数据源: SellerSprite MCP + 本地SQLite仓库
          </div>
        </div>
      `;
    }).join("");
  }
};
