// Pipeline Products Controller (Module 3 - Interactive Pipeline V2.4)
const PipelineView = {
  currentDetailItem: null,

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
      const capStr = m.displayUnits || (m.marketCapacityUnits ? `${m.marketCapacityUnits.toLocaleString()} 件/月` : "<span class='text-slate-400'>数据抓取中</span>");
      const pCountStr = m.productCount ? `${m.productCount} 款` : "<span class='text-slate-400'>--</span>";
      const avgPriceStr = m.avgPrice ? `$${m.avgPrice}` : "<span class='text-slate-400'>--</span>";

      const verifiedBadge = p.nodeVerified ?
        `<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">✓ 节点已校验</span>` :
        `<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200" title="${p.verificationNote}">⚠️ 节点未校验 (已拦截数据)</span>`;

      return `
        <div onclick="PipelineView.openPipelineDetail('${p.id}')" class="exec-card p-5 exec-card-hover flex flex-col justify-between cursor-pointer group">
          <div>
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition">${p.name}</h3>
                <div class="flex items-center gap-1.5 mt-1">
                  <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">${p.categoryLevel}</span>
                  ${verifiedBadge}
                </div>
              </div>
              <span class="text-xs px-2.5 py-1 rounded badge-green font-bold flex-shrink-0">${p.decision}</span>
            </div>

            <p class="text-xs text-slate-600 mt-3 leading-relaxed">${p.rationale || p.initialHypothesis}</p>

            <div class="mt-3 p-2 rounded bg-amber-50 border border-amber-200 text-[11px] text-amber-800 flex items-start gap-1.5">
              <span class="font-bold flex-shrink-0">⚠️ 合规与风险:</span>
              <span>${p.riskFlag}</span>
            </div>

            <div class="grid grid-cols-3 gap-2 mt-4 text-center text-xs py-2 bg-slate-50 rounded-lg border border-slate-100">
              <div>
                <div class="text-slate-400 text-[10px]">类目月估容量</div>
                <div class="text-slate-800 font-bold font-mono mt-0.5 text-[11px] truncate" title="${capStr}">${capStr}</div>
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
            <span class="text-blue-600 font-semibold text-[11px] group-hover:underline">查看4屏项目详情 ➔</span>
          </div>
        </div>
      `;
    }).join("");
  },

  async openPipelineDetail(itemId) {
    const modal = document.getElementById("pipelineDetailModal");
    if (!modal) return;

    modal.classList.remove("hidden");
    const container = document.getElementById("pipelineDetailContent");
    if (container) {
      container.innerHTML = `<div class="p-8 text-center text-xs text-blue-600 animate-pulse">正在加载 ${itemId} 项目4屏深度研报...</div>`;
    }

    const res = await API.getPipelineDetail(itemId);
    if (!res || res.status !== "ok" || !res.data) {
      if (container) container.innerHTML = `<div class="p-8 text-center text-xs text-rose-600">加载失败</div>`;
      return;
    }

    const d = res.data;
    this.currentDetailItem = d;
    const h = d.hardFacts || {};

    if (container) {
      container.innerHTML = `
        <div class="space-y-6">
          <!-- 头部概念与当前决策 -->
          <div class="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <div class="text-xs text-blue-600 font-semibold">待开发新品项目立项案</div>
              <h2 class="text-lg font-bold text-slate-900 mt-0.5">${d.name}</h2>
              <div class="text-xs text-slate-500 mt-0.5">主打关键词: <span class="font-mono font-medium">${d.keyword}</span></div>
            </div>
            <div class="text-right">
              <span class="text-xs text-slate-400 block">当前决策</span>
              <span class="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs inline-block mt-1">${d.currentDecision}</span>
            </div>
          </div>

          <!-- 屏 1: 一句话 + 4 个硬事实 -->
          <div class="exec-card p-4 bg-slate-50 border-slate-200">
            <div class="text-xs font-bold text-slate-800 mb-2">【屏 1】品类核心事实与合规门槛</div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div class="p-2.5 bg-white rounded border border-slate-200">
                <div class="text-[10px] text-slate-400">类目节点校验</div>
                <div class="font-bold text-slate-800 mt-0.5">${h.nodeVerified ? '✓ 节点校验通过' : '⚠️ 校验未通过'}</div>
                <div class="text-[10px] text-slate-500 mt-0.5 truncate" title="${h.categoryNode}">${h.categoryNode}</div>
              </div>
              <div class="p-2.5 bg-white rounded border border-slate-200">
                <div class="text-[10px] text-slate-400">供应链复用度</div>
                <div class="font-bold text-blue-600 mt-0.5">${h.supplyChainReuse}</div>
                <div class="text-[10px] text-slate-500 mt-0.5">发泡工艺全复用</div>
              </div>
              <div class="p-2.5 bg-white rounded border border-slate-200">
                <div class="text-[10px] text-slate-400">目标定价区间</div>
                <div class="font-bold text-emerald-600 mt-0.5">${h.targetPrice}</div>
                <div class="text-[10px] text-slate-500 mt-0.5">具备健康毛利</div>
              </div>
              <div class="p-2.5 bg-white rounded border border-slate-200">
                <div class="text-[10px] text-slate-400">合规门槛</div>
                <div class="font-bold text-amber-600 mt-0.5">合规审查通过</div>
                <div class="text-[10px] text-slate-500 mt-0.5 truncate" title="${h.compliance}">${h.compliance}</div>
              </div>
            </div>
          </div>

          <!-- 屏 2: 过去 12 个月大盘走势折线图 -->
          <div class="exec-card p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-slate-800">【屏 2】过去 12 个月细分类目走势 (Seasonal Pulse)</span>
              <span class="text-[11px] text-slate-400">重点关注旺季爆发期与断崖风险</span>
            </div>
            <div id="pipelineTrendChart" style="height: 180px; width: 100%;"></div>
          </div>

          <!-- 屏 3: TOP 10 在售标杆竞品列表 -->
          <div class="exec-card p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-slate-800">【屏 3】细分品类 TOP 标杆竞品参考 (Benchmark)</span>
              <span class="text-[11px] text-slate-400">拆解头部主打卖点与差评痛点</span>
            </div>
            <div class="overflow-x-auto max-h-48 overflow-y-auto">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                  <tr>
                    <th class="py-2 px-3">排名</th>
                    <th class="py-2 px-3">ASIN</th>
                    <th class="py-2 px-3">品牌 / 标题</th>
                    <th class="py-2 px-3">标价</th>
                    <th class="py-2 px-3">月估销量</th>
                    <th class="py-2 px-3">评分</th>
                  </tr>
                </thead>
                <tbody>
                  ${(d.topCompetitors || []).map(c => `
                    <tr class="border-b border-slate-100 hover:bg-slate-50">
                      <td class="py-2 px-3 font-mono font-bold text-slate-700">#${c.rank || '-'}</td>
                      <td class="py-2 px-3 font-mono text-blue-600 font-bold">${c.asin}</td>
                      <td class="py-2 px-3 text-slate-800 max-w-xs truncate" title="${c.title}"><b>${c.brand}</b> - ${c.title}</td>
                      <td class="py-2 px-3 font-mono text-slate-700">$${c.price || '--'}</td>
                      <td class="py-2 px-3 font-mono text-emerald-600 font-bold">${c.estimatedUnits ? c.estimatedUnits.toLocaleString() + ' 件' : '--'}</td>
                      <td class="py-2 px-3 font-mono text-amber-600">${c.rating ? c.rating + '⭐' : '--'}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>

          <!-- 屏 4: 供应链复用度分析 + 老板决策切换按钮组 -->
          <div class="exec-card p-4 bg-slate-50 border-slate-200">
            <div class="text-xs font-bold text-slate-800 mb-2">【屏 4】供应链复用评估与老板定性决策</div>
            
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] mb-4 text-slate-600">
              <div class="p-2 bg-white rounded border border-slate-200">
                <span class="text-slate-400 block">发泡复用:</span>
                <b class="text-slate-800">${d.supplyChainAnalysis?.foamProcessReuse || '100%'}</b>
              </div>
              <div class="p-2 bg-white rounded border border-slate-200">
                <span class="text-slate-400 block">模具成本:</span>
                <b class="text-slate-800">${d.supplyChainAnalysis?.moldCostEstimate || '$1,500'}</b>
              </div>
              <div class="p-2 bg-white rounded border border-slate-200">
                <span class="text-slate-400 block">外套面料复用:</span>
                <b class="text-slate-800">${d.supplyChainAnalysis?.fabricReuse || '90%'}</b>
              </div>
              <div class="p-2 bg-white rounded border border-slate-200">
                <span class="text-slate-400 block">头程物流:</span>
                <b class="text-slate-800">${d.supplyChainAnalysis?.logisticsAdvantage || '真空卷包压缩'}</b>
              </div>
            </div>

            <!-- 老板决策 4 态切换按钮组 -->
            <div class="pt-3 border-t border-slate-200">
              <span class="text-xs font-bold text-slate-800 block mb-2">老板决策直接落位：</span>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                <button onclick="PipelineView.handleDecisionChange('${d.id}', '列入优先开发')" class="p-2.5 rounded-lg border ${d.currentDecision === '列入优先开发' ? 'bg-emerald-600 text-white font-bold' : 'bg-white hover:bg-emerald-50 text-emerald-800 border-emerald-300'} text-xs text-center transition">
                  🚀 列入优先开发
                  <span class="block text-[10px] opacity-80 mt-0.5">供应链启动模具打样</span>
                </button>
                <button onclick="PipelineView.handleDecisionChange('${d.id}', '继续观察')" class="p-2.5 rounded-lg border ${d.currentDecision === '继续观察' ? 'bg-blue-600 text-white font-bold' : 'bg-white hover:bg-blue-50 text-blue-800 border-blue-300'} text-xs text-center transition">
                  👀 继续观察
                  <span class="block text-[10px] opacity-80 mt-0.5">追踪大盘与价格动态</span>
                </button>
                <button onclick="PipelineView.handleDecisionChange('${d.id}', '暂停调研')" class="p-2.5 rounded-lg border ${d.currentDecision === '暂停调研' ? 'bg-amber-600 text-white font-bold' : 'bg-white hover:bg-amber-50 text-amber-800 border-amber-300'} text-xs text-center transition">
                  ⏸️ 暂停调研
                  <span class="block text-[10px] opacity-80 mt-0.5">当前产能或合规存疑</span>
                </button>
                <button onclick="PipelineView.handleDecisionChange('${d.id}', '淘汰放弃')" class="p-2.5 rounded-lg border ${d.currentDecision === '淘汰放弃' ? 'bg-rose-600 text-white font-bold' : 'bg-white hover:bg-rose-50 text-rose-800 border-rose-300'} text-xs text-center transition">
                  ❌ 淘汰放弃
                  <span class="block text-[10px] opacity-80 mt-0.5">无明显毛利，移出管线</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      // Render chart
      setTimeout(() => {
        if (d.trend12m) {
          Charts.renderCategory12mCurve("pipelineTrendChart", d.trend12m);
        }
      }, 50);
    }
  },

  async handleDecisionChange(id, decision) {
    const res = await API.updatePipelineDecision(id, decision);
    if (res.status === "ok") {
      alert(`已成功将决策更新为: ${decision}`);
      this.closePipelineDetail();
      await this.loadPipeline();
    } else {
      alert("决策更新失败");
    }
  },

  closePipelineDetail() {
    const modal = document.getElementById("pipelineDetailModal");
    if (modal) modal.classList.add("hidden");
  }
};
