// Master Application Controller & Routing
const App = {
  currentView: "overview",

  init() {
    this.bindNavigation();
    this.handleRoute();
  },

  bindNavigation() {
    document.querySelectorAll("[data-nav]").forEach(el => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        const target = el.getAttribute("data-nav");
        if (el.classList.contains("disabled")) {
          alert("该模块为 Phase 2 规划中功能，当前阶段已置灰。");
          return;
        }
        this.navigateTo(target);
      });
    });

    const refreshBtn = document.getElementById("globalRefreshBtn");
    if (refreshBtn) {
      refreshBtn.onclick = async () => {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = `<span class="animate-spin mr-1">↻</span> 刷新中...`;
        await API.triggerDataRefresh();
        await this.handleRoute();
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = `<span>刷新数据</span>`;
      };
    }
  },

  navigateTo(viewName, param) {
    this.currentView = viewName;
    window.location.hash = viewName + (param ? `/${param}` : "");
    this.handleRoute();
  },

  async handleRoute() {
    const hash = window.location.hash.replace("#", "") || "overview";
    const parts = hash.split("/");
    const viewName = parts[0] || "overview";
    const viewParam = parts[1] || null;

    // Update Nav Sidebar styles
    document.querySelectorAll("[data-nav]").forEach(el => {
      if (el.getAttribute("data-nav") === viewName) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    });

    // Toggle View Sections
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.add("hidden"));
    const activeSec = document.getElementById(`view-${viewName}`);
    if (activeSec) {
      activeSec.classList.remove("hidden");
    }

    // Initialize Active View
    if (viewName === "overview") {
      await DashboardView.init();
    } else if (viewName === "market") {
      await MarketView.init();
    } else if (viewName === "products") {
      await ProductsView.init(viewParam);
    } else if (viewName === "pipeline") {
      await PipelineView.init();
    } else if (viewName === "opportunity") {
      await OpportunityView.init();
    } else if (viewName === "data-jobs") {
      await this.loadDataJobsView();
    }

    // Trigger charts resize after view visibility change
    setTimeout(() => Charts.resizeAll(), 120);
  },

  async loadDataJobsView() {
    const [jobsRes, statusRes] = await Promise.all([
      API.getDataJobs(),
      API.getAutomationStatus()
    ]);

    // 1. Update Automation Health Card
    if (statusRes && statusRes.status === "ok" && statusRes.data) {
      const s = statusRes.data;
      const statusDot = document.getElementById("automationStatusDot");
      const statusSummary = document.getElementById("automationStatusSummary");
      const nextRunEl = document.getElementById("autoNextRun");
      const lastStatusEl = document.getElementById("autoLastStatus");
      const targetsEl = document.getElementById("autoTargetsCount");

      if (statusSummary) {
        statusSummary.textContent = `每日 08:30 自动调度运行中 · 监控覆盖: 4核心SKU + ${s.confirmedCompetitorsCount || 0}已确认竞品 + 5类目标杆 + 细分大盘`;
      }
      if (nextRunEl) {
        nextRunEl.textContent = s.nextRunAt ? s.nextRunAt.slice(0, 16) : "明天 08:30";
      }
      if (lastStatusEl) {
        if (s.lastRunStatus === "success") {
          lastStatusEl.textContent = `正常完成 (${s.lastRunDurationSeconds || 0}秒)`;
          lastStatusEl.className = "text-xs font-bold text-emerald-600 mt-1";
          if (statusDot) statusDot.className = "w-3 h-3 rounded-full bg-emerald-500 animate-pulse";
        } else if (s.lastRunStatus === "partial") {
          lastStatusEl.textContent = `部分完成 (${s.lastRunItemsSuccess || 0}成功 / ${s.lastRunItemsFailed || 0}失败)`;
          lastStatusEl.className = "text-xs font-bold text-amber-600 mt-1";
          if (statusDot) statusDot.className = "w-3 h-3 rounded-full bg-amber-500 animate-pulse";
        } else {
          lastStatusEl.textContent = s.lastRunStatus || "待调度";
          lastStatusEl.className = "text-xs font-bold text-slate-700 mt-1";
        }
      }
      if (targetsEl) {
        targetsEl.textContent = `${s.monitoredTargetsCount || 10} 个关键业务对象`;
      }
    }

    // 2. Render Jobs Table
    const tbody = document.getElementById("jobsTableBody");
    if (!tbody || !jobsRes || !jobsRes.data) return;

    tbody.innerHTML = jobsRes.data.map(j => {
      let statusBadge = "badge-gray";
      if (j.status === "success") statusBadge = "badge-green";
      else if (j.status === "partial") statusBadge = "badge-amber";
      else if (j.status === "failed") statusBadge = "badge-rose";

      const durationStr = (j.duration_seconds !== null && j.duration_seconds !== undefined) ? `${j.duration_seconds}s` : "--";
      const itemsStr = (j.items_total) ? `${j.items_success || 0}成功 / ${j.items_failed || 0}失败 (共${j.items_total})` : "--";

      return `
        <tr class="hover:bg-slate-50 text-xs border-b border-slate-100 transition">
          <td class="py-2.5 px-4 font-mono font-bold text-slate-800">${j.job_name}</td>
          <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${statusBadge}">${j.status}</span></td>
          <td class="py-2.5 px-4 font-mono text-slate-600">${durationStr}</td>
          <td class="py-2.5 px-4 font-mono text-slate-600">${itemsStr}</td>
          <td class="py-2.5 px-4 font-mono text-slate-500">${j.run_at}</td>
          <td class="py-2.5 px-4 text-slate-700 max-w-sm truncate" title="${j.result_summary || ''}">${j.result_summary || '--'}</td>
        </tr>
      `;
    }).join("");
  },

  async triggerManualJob() {
    const btn = document.getElementById("btnManualTriggerRefresh");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="animate-spin mr-1">↻</span> 执行快照抓取中...`;
    }

    await API.triggerDataRefresh();
    await this.loadDataJobsView();

    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>⚡ 立即执行全量快照</span>`;
    }
  }
};

window.addEventListener("hashchange", () => App.handleRoute());
document.addEventListener("DOMContentLoaded", () => App.init());
