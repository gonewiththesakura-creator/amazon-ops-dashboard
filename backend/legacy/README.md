# ⚠️ 历史废弃代码归档 (Deprecated Legacy Code)

本目录归档了 V1 版本早期的原型服务代码。
包含模拟数据兜底（Fallback）与旧版未规范化的 MCP 调用逻辑。

## 归档文件说明
* `asin_service.py`：V1 ASIN 查询服务（已被 `backend/services/core_product_service.py` 替代）
* `market_service.py`：V1 粗颗粒度类目查询（已被 `backend/services/core_market_service.py` 替代）
* `keyword_service.py`：V1 关键词查询（已被 `backend/services/opportunity_lab_service.py` 替代）
* `ai_diagnostics.py`：V1 伪评分雷达图逻辑（已被 `backend/services/rule_diagnostics.py` 严格事实推理替代）
* `pipeline_products.py`：V1 简单管线逻辑（已被 `backend/services/pipeline_service.py` 替代）

## 声明
**禁止在 V2.1+ 生产环境中调用本目录内的任何模块。**
所有当前活跃路由与功能均使用 `backend/services/` 下严格践行“零伪造数据”的 V2.1 现代服务。
