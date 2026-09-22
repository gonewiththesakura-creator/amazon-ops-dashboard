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
    container.innerHTML = projects.map(p => {
      const plan = p.plan || {};
      const findings = p.findings || {};
      const levels = plan.categoryLevels || [];
      const opps = findings.opportunities || [];
      const risks = findings.risks || [];
      const actions = findings.nextActions || [];

      return `
        <div class="exec-card p-5 mb-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
            <div>
              <h3 class="text-sm font-bold text-slate-900">${p.title}</h3>
              <p class="text-xs text-slate-500 mt-0.5">老板原提问: "${p.user_question || '--'}"</p>
            </div>
            <span class="text-xs px-2.5 py-1 rounded badge-blue font-bold self-start sm:self-auto">
              ${p.status === 'completed' ? '调研完成' : p.status}
            </span>
          </div>

          <!-- Discovered Category Breadcrumbs -->
          <div class="mt-3 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500 font-mono">
            <span class="font-bold text-slate-700">探测类目层级:</span>
            ${levels.map((lvl, idx) => `
              <span class="bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-slate-800">${lvl}</span>
              ${idx < levels.length - 1 ? '<span class="text-slate-400">➔</span>' : ''}
            `).join("")}
          </div>

          <!-- AI Findings -->
          <div class="mt-3.5 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div class="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200/60">
              <div class="font-bold text-emerald-800 flex items-center gap-1">
                <span>✓ 核心机会点</span>
              </div>
              <ul class="mt-1.5 space-y-1 text-slate-700 leading-relaxed">
                ${opps.map(o => `<li>• ${o}</li>`).join("")}
              </ul>
            </div>

            <div class="p-3 rounded-lg bg-rose-50/60 border border-rose-200/60">
              <div class="font-bold text-rose-800 flex items-center gap-1">
                <span>⚠️ 风险提示</span>
              </div>
              <ul class="mt-1.5 space-y-1 text-slate-700 leading-relaxed">
                ${risks.map(r => `<li>• ${r}</li>`).join("")}
              </ul>
            </div>
          </div>

          <!-- Action Steps -->
          ${actions.length > 0 ? `
            <div class="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
              <span class="font-bold text-slate-900 block mb-1">🎯 建议下一步行动路径:</span>
              <div class="space-y-1">
                ${actions.map(act => `<div>${act}</div>`).join("")}
              </div>
            </div>
          ` : ''}

          <div class="mt-3 text-[11px] text-slate-400 text-right">
            创建时间: ${p.created_at || '--'}
          </div>
        </div>
      `;
    }).join("");
  }
};
