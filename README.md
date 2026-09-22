# 亚马逊 AI 选品情报与决策中心 (Amazon AI Opportunity Intelligence) V2

基于卖家精灵（SellerSprite）专业 MCP 接口构建的跨境电商选品情报、竞品穿透与决策中心。
全面重构自 2026-09-09 战略会议草稿与运营蓝图，严格践行 **“零伪造数据 (Zero Fake Data)”** 与 **“高管浅色决策视图”** 准则。

---

## 🌟 核心业务架构与四大板块

系统彻底分离大盘宏观分析、核心 SKU 战情、供应链衍生产品与新赛道机会探索，重构为四大专业业务板块：

### ① 现有记忆棉枕头市场大盘 (Core Market)
* **直达四级细分节点**：直接穿透至 `Home & Kitchen > Bedding > Bed Pillows & Positioners > Neck & Cervical Pillows (颈椎枕 / 蝴蝶枕: 1055398:1063252:1199122:3732111)`。
* **CR4 / CR8 品牌集中度**：实时调取大盘品牌销量占比，客观呈现垄断格局（如 Derila 等头部品牌占有率）。
* **真实价格带机会分析**：统计各价格区间（如 $20-$30, $40-$50）的在售商品数与销量占比，寻找错位竞争蓝海。
* **卖家属地与评分分布**：中国跨境卖家与本土卖家比例分析，全类目星级评分真实分布。

### ② 现有 4 个记忆棉枕头 SKU 战情室 (Core 4 SKUs War Room)
* **聚焦 4 个记忆棉枕头核心 SKU**：
  1. `LIU-B0GYH8WT22` / 刘总枕头 (`B0GYH8WT22`，独立款，Parent ASIN 隔离)
  2. `ELOVNOVA-Gray` / 江西灰色 (`B0GY2TDLTZ`，变体款，Parent: `B0GY2VPQPD`)
  3. `ELOVNOVA-Blue` / 江西蓝色 (`B0GY2WGTDM`，变体款，Parent: `B0GY2VPQPD`)
  4. `PENDING-SKU-04` / 待配置核心枕头 SKU（真实保留槽位，绝不胡乱捏造数据）
* **标量级 BSR 与价格走势**：修复数据类型解析，保证 BSR 为纯整型数字（彻底告别 `[object Object]`），真实时间序列走势。
* **四大竞品池细分**：
  * **直接同款竞品 (Direct)**：同材质、同形态（如蝴蝶枕）直接对位商品。
  * **头部标杆 (Benchmark)**：类目销量前 3 领跑标杆（如 Derila）。
  * **异动飙升 (Fast Growth)**：30 天排名跳升最快的黑马竞品。
  * **Top 100 参照池 (Category Pool)**：全类目前 100 名多维大盘参照。
* **市场相对表现诊断**：跑赢市场（Outperforming）、持平大盘（Par）、跑输大盘（Underperforming）。

### ③ 记忆棉供应链相关待开发产品 (Supply Chain Pipeline)
* **复用现有慢回弹记忆棉注塑/发泡产线**（模具周期 20-30 天）：
  * **人体工学腰靠腰枕 (Lumbar Support Pillow)**：深耕久坐办公与车载场景（如现有的 `B0HJWZM439` / `B0HJX1MGBF`）。
  * **U型便携旅行枕 (Travel & Neck Pillow)**：差旅刚需高频场景。
  * **记忆棉减压坐垫 (Seat Cushion)**：人体工学办公套装延伸。
  * **电动加热揉捏按摩枕 (Electric Massage Pillow)**：高溢价款，带电合规与退货率严格把控。
* **真实大盘容量测算**：自动挂载四级节点真实销售体量、均价与可行性决策结论。

### ④ 新赛道机会实验室 (Opportunity Lab)
* **自然语言选品意图探索**（例如：*“我想了解一下儿童防驼背矫正坐垫的市场机会与竞争情况”*）。
* **自动化情报探针**：
  1. 语义理解与意图提取（确定目标关键词、市场范围）。
  2. 逆向推导亚马逊类目树层级与四级细分节点。
  3. 调取真实搜索趋势与客单价测算。
  4. 输出结构化调研报告（结论、机遇点、风险提示、落地三步法），并持久化沉淀于数据库。

---

## 🛡️ 核心准则与工程质量 (P0)

1. **零伪造数据 (Zero Fake Data)**：
   - 彻底废除任何模拟占位数据（绝不默认填充 $45.99 或 4.2 星）。
   - 外部数据暂缺时，接口统一返回 `status: "unavailable"` / `data: null`，前端展示友好空状态，绝不捏造平滑曲线。
2. **安全隔离**：
   - 杜绝硬编码 API 密钥，所有密钥统一保存在本地 `.env` 文件。
   - MCP 协议通过 HTTP 请求头 `secret-key` 鉴权，URL 参数不携带任何敏感 Token。
   - `.env` 与数据库文件已被 `.gitignore` 保护。
3. **真实 SQLite 数据持久化**：
   - 本地 `v2_store.db` 记录 ASIN 历史快照、大盘快照、竞品池、储备产品与选品调研报告。
4. **高管浅色决策 UI**：
   - 告别刺眼暗黑霓虹，采用沉稳明快的 `#F6F7F9` 高管浅色质感界面，支持 10 秒决策速览简报。

---

## 🚀 极速启动指南

### 1. 环境准备
确保已安装 Python 3.10+。克隆项目后安装基础依赖：

```bash
cd amazon-ops-dashboard
pip install fastapi uvicorn httpx pydantic
```

### 2. 配置环境变量
复制配置样例并填入您的卖家精灵 MCP 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
SELLERSPRITE_MCP_URL=https://mcp.sellersprite.com/mcp
SELLERSPRITE_MCP_SECRET=your_sellersprite_secret_key_here
HOST=127.0.0.1
PORT=8000
```

### 3. 一键启动服务
```bash
python start.py
```
启动后自动在浏览器打开：
👉 **http://127.0.0.1:8000**

### 4. 运行全链路测试套件
```bash
python test_server.py
```
一键验证 10 项核心测试集（安全隔离、大盘穿透、4 SKU 标量 BSR 解析、竞品池、选品实验室、零伪造机制）。

---

## 📁 现代化模块结构

```text
.
├── backend/
│   ├── config.py                      # 安全环境变量配置 (P0)
│   ├── database.py                    # SQLite 核心模型与历史快照存储
│   ├── mcp_client.py                  # 卖家精灵异步 MCP 客户端 (请求头鉴权)
│   ├── cache.py                       # 本地查询缓存 (保护 API 配额)
│   ├── main.py                        # 21 个 REST API 路由控制器
│   └── services/
│       ├── core_market_service.py     # 模块①：记忆棉四级类目大盘服务
│       ├── core_product_service.py    # 模块②：4 个核心 SKU 战情与 4 大竞品池
│       ├── pipeline_service.py        # 模块③：记忆棉供应链衍生待开发产品
│       ├── opportunity_lab_service.py # 模块④：新赛道意图驱动选品实验室
│       ├── rule_diagnostics.py        # 10秒决策简报与规则事实推理引擎
│       ├── data_job_service.py        # 数据采集与定时任务监控
│       └── replenishment_service.py   # Phase 2 补货与资金池测算模型
├── frontend/
│   ├── index.html                     # 高管浅色响应式看板 (固定左侧导航)
│   ├── styles.css                     # 浅色商务主题与卡片排版
│   ├── echarts.min.js                 # 本地 Apache ECharts 渲染引擎
│   ├── tailwind.min.js                # 本地 Tailwind CSS 引擎
│   └── js/
│       ├── api.js                     # 统一 API 请求封装
│       ├── charts.js                  # ECharts 图表渲染组件
│       ├── dashboard.js               # 10秒决策简报控制器
│       ├── market.js                  # 模块① 市场大盘视图控制器
│       ├── products.js                # 模块② 核心 4 SKU 战情室控制器
│       ├── pipeline.js                # 模块③ 供应链产品控制器
│       ├── opportunity.js             # 模块④ 新赛道实验室控制器
│       └── app.js                     # 全局路由与视图切换总控
├── .env.example                       # 环境变量配置模板 (无敏感泄露)
├── .gitignore                         # 忽略 .env, *.db 等敏感文件
├── start.py                           # 一键启动服务与浏览器调起
├── test_server.py                     # 全功能自动化单元与集成测试
└── README.md                          # 系统架构与使用说明
```
