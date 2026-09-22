// API requester module with unified error handling
const API = {
  async get(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }
      return await res.json();
    } catch (e) {
      console.error(`API GET error [${url}]:`, e);
      return { status: "error", error: e.message, data: null };
    }
  },

  async post(url, payload) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }
      return await res.json();
    } catch (e) {
      console.error(`API POST error [${url}]:`, e);
      return { status: "error", error: e.message, data: null };
    }
  },

  // Endpoints
  getBriefing() {
    return this.get("/api/dashboard/briefing");
  },

  getMarketOverview(nodeIdPath = "1055398:1063252:1199122:3732111") {
    return this.get(`/api/core-market/overview?nodeIdPath=${encodeURIComponent(nodeIdPath)}`);
  },

  getMarketTree() {
    return this.get("/api/core-market/tree");
  },

  getCoreProducts() {
    return this.get("/api/core-products");
  },

  getCoreProductsComparison() {
    return this.get("/api/core-products/comparison");
  },

  getProductDetail(asin) {
    return this.get(`/api/core-products/${asin}`);
  },

  getProductCompetitors(asin) {
    return this.get(`/api/core-products/${asin}/competitors`);
  },

  getPipeline() {
    return this.get("/api/pipeline");
  },

  addPipeline(payload) {
    return this.post("/api/pipeline", payload);
  },

  getResearchProjects() {
    return this.get("/api/research");
  },

  conductResearch(userQuestion) {
    return this.post("/api/research", { userQuestion });
  },

  getDataJobs() {
    return this.get("/api/data-jobs");
  },

  getAutomationStatus() {
    return this.get("/api/data-jobs/status");
  },

  triggerDataRefresh() {
    return this.post("/api/data-jobs/refresh", {});
  },

  addManualCompetitor(asin, competitorAsin, notes = "手工添加直接竞品") {
    return this.post(`/api/core-products/${asin}/competitors/manual`, { competitorAsin, notes });
  },

  confirmCompetitor(asin, competitorAsin) {
    return this.post(`/api/core-products/${asin}/competitors/confirm`, { competitorAsin });
  },

  async deleteCompetitor(asin, competitorAsin) {
    try {
      const res = await fetch(`/api/core-products/${asin}/competitors/${competitorAsin}`, {
        method: "DELETE"
      });
      return await res.json();
    } catch (e) {
      console.error("API DELETE error:", e);
      return { status: "error", error: e.message };
    }
  }
};
