// API requester module with unified error handling
const API = {
  async get(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        let errMsg = `HTTP ${res.status}`;
        try {
          const j = await res.json();
          errMsg = j.detail || j.error || errMsg;
        } catch (_) {
          errMsg = await res.text();
        }
        return { status: "error", error: errMsg, data: null };
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
        let errMsg = `HTTP ${res.status}`;
        try {
          const j = await res.json();
          errMsg = j.detail || j.error || errMsg;
        } catch (_) {
          errMsg = await res.text();
        }
        return { status: "error", error: errMsg, data: null };
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

  // V2.4 & V2.5 Endpoints
  getDashboardTrends(range = "12m") {
    return this.get(`/api/dashboard/trends?range=${range}`);
  },

  getPipelineDetail(id) {
    return this.get(`/api/pipeline/${encodeURIComponent(id)}`);
  },

  updatePipelineDecision(id, decision, rationale = "") {
    return this.post(`/api/pipeline/${encodeURIComponent(id)}/decision`, { decision, rationale });
  },

  triggerPipelineResearch(id) {
    return this.post(`/api/pipeline/${encodeURIComponent(id)}/research`, {});
  },

  collectAsinPackage(asin, forceRefresh = false) {
    return this.post("/api/collection/asin", { asin, forceRefresh });
  },

  collectCategoryPackage(nodeIdPath, forceRefresh = false) {
    return this.post("/api/collection/category", { nodeIdPath, forceRefresh });
  },

  collectKeywordsPackage(keywords) {
    return this.post("/api/collection/keywords", { keywords });
  },

  collectBatchAsins(asins) {
    return this.post("/api/collection/batch-asins", { asins });
  },

  getCollectionJob(jobId) {
    return this.get(`/api/collection/jobs/${jobId}`);
  },

  listCollectionJobs() {
    return this.get("/api/collection/jobs");
  },

  getCollectionTools() {
    return this.get("/api/collection/tools");
  },

  scanCollectionTools() {
    return this.post("/api/collection/scan-tools", {});
  },

  getAssetStats() {
    return this.get("/api/assets/stats");
  },

  searchAssets(q, type = null) {
    let url = `/api/assets/search?q=${encodeURIComponent(q)}`;
    if (type) url += `&type=${encodeURIComponent(type)}`;
    return this.get(url);
  },

  getRawAsset(rawId) {
    return this.get(`/api/assets/raw/${rawId}`);
  },

  addManualCompetitor(asin, competitorAsin, notes = "手工添加直接竞品") {
    return this.post(`/api/core-products/${asin}/competitors/manual`, { competitorAsin, notes });
  },

  confirmCompetitor(asin, competitorAsin) {
    return this.post(`/api/core-products/${asin}/competitors/confirm`, { competitorAsin });
  },

  ignoreCompetitor(asin, competitorAsin) {
    return this.post(`/api/core-products/${asin}/competitors/${competitorAsin}/ignore`, {});
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
