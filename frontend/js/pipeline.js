// Pipeline Products Controller (Module 3)
const PipelineView = {
  async init() {
    await this.loadPipeline();
  },

  async loadPipeline() {
    const loading = document.getElementById("pipelineLoading");
    if (loading) loading.classList.remove("hidden");

    const res = await API.getPipeline();
    if (loading) loading.classList.add("hidden");

    const container = document.getElementById("pipelineContainer");
    if (!container || !res || res.status !== "ok" || !res.data) return;

    const candidates = res.data.candidates || [];
    container.innerHTML = candidates.map(p => {
      const m = p.metrics || {};
      const capStr = m.marketCapacityUnits ? `${m.marketCapacityUnits.toLocaleString()} 件/月` : "<span class='text-slate-400'>数据抓取中</span>";
      const pCountStr = m.productCount ? `${m.productCount} 款` : "<span class='text-slate-400'>--</span>";
      const avgPriceStr = m.avgPrice ? `$${m.avgPrice}` : "<span class='text-slate-400'>--</span>";

      return `
        <div class="exec-card p-5 exec-card-hover flex flex-col justify-between">
          <div>
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="text-sm font-bold text-slate-900">${p.name}</h3>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 mt-1 inline-block">${p.categoryLevel}</span>
              </div>
              <span class="text-xs px-2.5 py-1 rounded badge-green font-bold">${p.decision}</span>
            </div>

            <p class="text-xs text-slate-600 mt-3 leading-relaxed">${p.rationale}</p>

            <div class="mt-3 p-2 rounded bg-amber-50 border border-amber-200 text-[11px] text-amber-800 flex items-start gap-1.5">
              <span class="font-bold flex-shrink-0">⚠️ 风险标记:</span>
              <span>${p.riskFlag}</span>
            </div>

            <div class="grid grid-cols-3 gap-2 mt-4 text-center text-xs py-2 bg-slate-50 rounded-lg border border-slate-100">
              <div>
                <div class="text-slate-400 text-[10px]">类目月估销量</div>
                <div class="text-slate-800 font-bold font-mono mt-0.5">${capStr}</div>
              </div>
              <div>
                <div class="text-slate-400 text-[10px]">在售竞品数</div>
                <div class="text-slate-800 font-bold font-mono mt-0.5">${pCountStr}</div>
              </div>
              <div>
                <div class="text-slate-400 text-[10px]">均价参考</div>
                <div class="text-slate-800 font-bold font-mono mt-0.5">${avgPriceStr}</div>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>状态: <span class="font-semibold text-slate-700">${p.status}</span></span>
            <span class="text-blue-600 font-medium">利用现有记忆棉发泡产线</span>
          </div>
        </div>
      `;
    }).join("");
  }
};
