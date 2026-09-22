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
    const res = await API.getDataJobs();
    const tbody = document.getElementById("jobsTableBody");
    if (!tbody || !res || !res.data) return;

    tbody.innerHTML = res.data.map(j => `
      <tr class="hover:bg-slate-50 text-xs border-b border-slate-100">
        <td class="py-2.5 px-4 font-mono font-bold text-slate-800">${j.job_name}</td>
        <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${j.status === 'success' ? 'badge-green' : 'badge-rose'}">${j.status}</span></td>
        <td class="py-2.5 px-4 font-mono text-slate-500">${j.run_at}</td>
        <td class="py-2.5 px-4 text-slate-700">${j.result_summary || '--'}</td>
      </tr>
    `).join("");
  }
};

window.addEventListener("hashchange", () => App.handleRoute());
document.addEventListener("DOMContentLoaded", () => App.init());
