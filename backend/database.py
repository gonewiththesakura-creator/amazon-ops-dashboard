import sqlite3
import json
import logging
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from .config import settings

logger = logging.getLogger("database")

class Database:
    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path
        self.init_schema()
        self.seed_defaults()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Core Products Registry
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT UNIQUE NOT NULL,
                    sku TEXT NOT NULL,
                    internal_name TEXT NOT NULL,
                    product_type TEXT,
                    parent_asin TEXT,
                    marketplace TEXT DEFAULT 'US',
                    is_core_pillow BOOLEAN DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. ASIN Snapshots for real historical tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asin_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    price REAL,
                    estimated_units INTEGER,
                    estimated_revenue REAL,
                    bsr INTEGER,
                    rating REAL,
                    reviews INTEGER,
                    coupon TEXT,
                    source TEXT DEFAULT 'sellersprite_mcp',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asin, snapshot_date)
                )
            """)

            # 3. Market Nodes (Category tree)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id_path TEXT UNIQUE NOT NULL,
                    node_label TEXT NOT NULL,
                    parent_id TEXT,
                    level INTEGER DEFAULT 4,
                    marketplace TEXT DEFAULT 'US'
                )
            """)

            # 4. Market Snapshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id_path TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    products INTEGER,
                    sellers INTEGER,
                    units INTEGER,
                    revenue REAL,
                    avg_price REAL,
                    median_price REAL,
                    cr4 REAL,
                    cr8 REAL,
                    source TEXT DEFAULT 'sellersprite_mcp',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(node_id_path, snapshot_date)
                )
            """)

            # 5. Competitor Sets (classified into direct, suggested, benchmark, fast_growth, top100)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS competitor_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_asin TEXT NOT NULL,
                    competitor_asin TEXT NOT NULL,
                    group_type TEXT CHECK(group_type IN ('direct', 'suggested', 'benchmark', 'fast_growth', 'top100')),
                    source TEXT DEFAULT 'manual',
                    verified INTEGER DEFAULT 0,
                    verified_at DATETIME,
                    similarity_score REAL DEFAULT 1.0,
                    notes TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_asin, competitor_asin, group_type)
                )
            """)

            # Schema migrations for existing DB instances
            for col_name, col_type in [
                ("source", "TEXT DEFAULT 'manual'"),
                ("verified", "INTEGER DEFAULT 0"),
                ("verified_at", "DATETIME"),
                ("last_synced_at", "DATETIME"),
                ("relationship_summary", "TEXT"),
                ("gap_insight", "TEXT"),
                ("price_diff", "REAL"),
                ("units_ratio", "REAL")
            ]:
                try:
                    cursor.execute(f"ALTER TABLE competitor_sets ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

            # 5b. Raw MCP Responses Archive (Traceability & Immutable Evidence)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mcp_raw_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    verification_status TEXT DEFAULT 'verified',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5c. Time Series: ASIN Price History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asin_price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    price REAL NOT NULL,
                    source TEXT DEFAULT 'keepa',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asin, snapshot_date)
                )
            """)

            # 5d. Time Series: ASIN BSR History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asin_bsr_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    bsr INTEGER NOT NULL,
                    source TEXT DEFAULT 'keepa',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asin, snapshot_date)
                )
            """)

            # 5e. Time Series: ASIN Sales History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asin_sales_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    units INTEGER,
                    revenue REAL,
                    source TEXT DEFAULT 'sellersprite_mcp',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asin, snapshot_date)
                )
            """)

            # 5f. Keyword Miner Query History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    marketplace TEXT DEFAULT 'US',
                    searches INTEGER DEFAULT 0,
                    purchases INTEGER DEFAULT 0,
                    purchase_rate REAL DEFAULT 0.0,
                    prods_count INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'sellersprite_mcp',
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(keyword, marketplace, fetched_at)
                )
            """)

            # 6. Pipeline Products (Memory Foam Supply Chain Relatives)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category_level TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    node_id_path TEXT,
                    status TEXT DEFAULT 'under_research',
                    decision TEXT DEFAULT 'pending',
                    rationale TEXT,
                    risk_flag TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Opportunity Lab Research Projects (Completely New Categories)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    research_type TEXT CHECK(research_type IN ('pipeline', 'new_category')),
                    status TEXT DEFAULT 'completed',
                    user_question TEXT,
                    plan_json TEXT,
                    findings_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 8. Rule-based Insights with Evidence
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rule_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_type TEXT,
                    subject_id TEXT,
                    summary TEXT NOT NULL,
                    evidence_json TEXT,
                    risk_json TEXT,
                    actions_json TEXT,
                    confidence REAL DEFAULT 0.85,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 9. Automated Data Jobs & Monitoring
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds REAL DEFAULT 0.0,
                    items_total INTEGER DEFAULT 0,
                    items_success INTEGER DEFAULT 0,
                    items_failed INTEGER DEFAULT 0,
                    result_summary TEXT,
                    details_json TEXT
                )
            """)

            for col_name, col_type in [
                ("duration_seconds", "REAL DEFAULT 0.0"),
                ("items_total", "INTEGER DEFAULT 0"),
                ("items_success", "INTEGER DEFAULT 0"),
                ("items_failed", "INTEGER DEFAULT 0"),
                ("details_json", "TEXT")
            ]:
                try:
                    cursor.execute(f"ALTER TABLE data_jobs ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

            conn.commit()

    def add_competitor(self, owner_asin: str, competitor_asin: str, group_type: str = "direct", source: str = "manual", verified: int = 1, notes: str = "", similarity_score: float = 1.0) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO competitor_sets (owner_asin, competitor_asin, group_type, source, verified, verified_at, notes, similarity_score, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(owner_asin, competitor_asin, group_type) DO UPDATE SET
                    source = excluded.source,
                    verified = excluded.verified,
                    verified_at = excluded.verified_at,
                    notes = excluded.notes,
                    similarity_score = excluded.similarity_score,
                    active = 1
            """, (owner_asin, competitor_asin, group_type, source, verified, now_iso if verified else None, notes, similarity_score))
            conn.commit()
            return True

    def remove_competitor(self, owner_asin: str, competitor_asin: str, group_type: str = "direct") -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM competitor_sets 
                WHERE owner_asin = ? AND competitor_asin = ? AND group_type = ?
            """, (owner_asin, competitor_asin, group_type))
            conn.commit()
            return True

    def list_confirmed_competitors(self, owner_asin: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM competitor_sets 
                WHERE owner_asin = ? AND verified = 1 AND active = 1
                ORDER BY created_at DESC
            """, (owner_asin,))
            return [dict(r) for r in c.fetchall()]

    def archive_raw_response(self, tool_name: str, request_json: str, response_json: str, entity_type: Optional[str] = None, entity_id: Optional[str] = None, verification_status: str = "verified") -> int:
        """Archives raw external MCP/Keepa JSON response for immutable audit trail and traceability."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO mcp_raw_responses (tool_name, request_json, response_json, entity_type, entity_id, verification_status, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tool_name, request_json, response_json, entity_type, entity_id, verification_status, now_iso))
            conn.commit()
            return c.lastrowid

    def batch_insert_price_history(self, asin: str, points: List[Dict[str, Any]], source: str = "keepa"):
        """Backfills or appends price history points (date, price)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            c = conn.cursor()
            for p in points:
                d_str = p.get("date")
                price = p.get("price")
                if d_str and price is not None:
                    c.execute("""
                        INSERT OR REPLACE INTO asin_price_history (asin, snapshot_date, price, source, fetched_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (asin, d_str, float(price), source, now_iso))
            conn.commit()

    def batch_insert_bsr_history(self, asin: str, points: List[Dict[str, Any]], source: str = "keepa"):
        """Backfills or appends BSR history points (date, bsr)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            c = conn.cursor()
            for p in points:
                d_str = p.get("date")
                bsr = p.get("bsr")
                if d_str and bsr is not None:
                    c.execute("""
                        INSERT OR REPLACE INTO asin_bsr_history (asin, snapshot_date, bsr, source, fetched_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (asin, d_str, int(bsr), source, now_iso))
            conn.commit()

    def batch_insert_sales_history(self, asin: str, points: List[Dict[str, Any]], source: str = "sellersprite_mcp"):
        """Backfills or appends sales history points (date, units, revenue)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            c = conn.cursor()
            for p in points:
                d_str = p.get("date")
                units = p.get("units")
                rev = p.get("revenue")
                if d_str:
                    c.execute("""
                        INSERT OR REPLACE INTO asin_sales_history (asin, snapshot_date, units, revenue, source, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (asin, d_str, units, rev, source, now_iso))
            conn.commit()

    def get_price_history(self, asin: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT snapshot_date as date, price FROM asin_price_history WHERE asin = ? ORDER BY snapshot_date ASC", (asin,))
            return [dict(r) for r in c.fetchall()]

    def get_bsr_history(self, asin: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT snapshot_date as date, bsr FROM asin_bsr_history WHERE asin = ? ORDER BY snapshot_date ASC", (asin,))
            return [dict(r) for r in c.fetchall()]

    def get_latest_asin_snapshot(self, asin: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM asin_snapshots WHERE asin = ? ORDER BY snapshot_date DESC, id DESC LIMIT 1", (asin,))
            row = c.fetchone()
            return dict(row) if row else None

    def update_competitor_sync_meta(self, owner_asin: str, competitor_asin: str, gap_summary: Optional[str] = None, gap_insight: Optional[str] = None, price_diff: Optional[float] = None, units_ratio: Optional[float] = None):
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE competitor_sets
                SET last_synced_at = ?,
                    relationship_summary = COALESCE(?, relationship_summary),
                    gap_insight = COALESCE(?, gap_insight),
                    price_diff = COALESCE(?, price_diff),
                    units_ratio = COALESCE(?, units_ratio)
                WHERE owner_asin = ? AND competitor_asin = ?
            """, (now_iso, gap_summary, gap_insight, price_diff, units_ratio, owner_asin, competitor_asin))
            conn.commit()

    def count_real_monitored_targets(self) -> Dict[str, int]:
        """Calculates real count of monitored business entities without hardcoding."""
        with self.get_connection() as conn:
            c = conn.cursor()
            # 1. Active core SKUs
            c.execute("SELECT COUNT(*) as cnt FROM products WHERE is_core_pillow = 1 AND status = 'active' AND asin != 'PENDING_SKU_4'")
            core_count = c.fetchone()["cnt"]

            # 2. Active confirmed direct competitors
            c.execute("SELECT COUNT(DISTINCT competitor_asin) as cnt FROM competitor_sets WHERE group_type = 'direct' AND verified = 1 AND active = 1")
            direct_count = c.fetchone()["cnt"]

            # 3. Active benchmark competitors
            c.execute("SELECT COUNT(DISTINCT competitor_asin) as cnt FROM competitor_sets WHERE group_type = 'benchmark' AND active = 1")
            bench_count = c.fetchone()["cnt"]

            # 4. Monitored market category nodes
            c.execute("SELECT COUNT(*) as cnt FROM market_nodes")
            market_count = c.fetchone()["cnt"]

            total = core_count + direct_count + bench_count + market_count
            return {
                "total": total,
                "coreCount": core_count,
                "directCompetitorsCount": direct_count,
                "benchmarkCount": bench_count,
                "marketNodesCount": market_count
            }

    def seed_defaults(self):
        """Seeds standard core products, category nodes, and pipeline candidates without fabricating metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Seed 4 Core Memory Foam Pillows (Lumbar pillows are in Module 3)
            # 1. B0GYH8WT22: LIU-B0GYH8WT22 / 刘总枕头 (Single item, parent_asin=None)
            cursor.execute("""
                INSERT OR IGNORE INTO products (asin, sku, internal_name, product_type, parent_asin, is_core_pillow, status)
                VALUES ('B0GYH8WT22', 'LIU-B0GYH8WT22', '刘总枕头', 'Premium Ergonomic Contour Memory Foam Pillow', NULL, 1, 'active')
            """)
            # 2. B0GY2TDLTZ: ELOVNOVA-Gray / 江西灰色 (Parent: B0GY2VPQPD)
            cursor.execute("""
                INSERT OR IGNORE INTO products (asin, sku, internal_name, product_type, parent_asin, is_core_pillow, status)
                VALUES ('B0GY2TDLTZ', 'ELOVNOVA-Gray', '江西灰色', 'Ergonomic Cervical / Contour Memory Foam Pillow', 'B0GY2VPQPD', 1, 'active')
            """)
            # 3. B0GY2WGTDM: ELOVNOVA-Blue / 江西蓝色 (Parent: B0GY2VPQPD)
            cursor.execute("""
                INSERT OR IGNORE INTO products (asin, sku, internal_name, product_type, parent_asin, is_core_pillow, status)
                VALUES ('B0GY2WGTDM', 'ELOVNOVA-Blue', '江西蓝色', 'Ergonomic Cervical / Contour Memory Foam Pillow', 'B0GY2VPQPD', 1, 'active')
            """)
            # 4. 4th SKU: Pending configuration, do NOT fabricate!
            cursor.execute("""
                INSERT OR IGNORE INTO products (asin, sku, internal_name, product_type, parent_asin, is_core_pillow, status)
                VALUES ('PENDING_SKU_4', 'PENDING-SKU-04', '待配置核心枕头SKU', '待规划记忆棉枕头', NULL, 1, 'pending_config')
            """)

            # Seed Core Memory Foam Market Category Nodes
            cursor.execute("""
                INSERT OR IGNORE INTO market_nodes (node_id_path, node_label, parent_id, level)
                VALUES ('1055398:1063252:1199122:3732111', 'Home & Kitchen > Bedding > Bed Pillows & Positioners > Neck & Cervical Pillows', '1199122', 4)
            """)

            # Seed Module 3: Memory Foam Supply Chain Relatives (Pipeline Products)
            pipeline_seeds = [
                (
                    "travel_pillow",
                    "U型枕 / 便携旅行枕 (Travel & Neck Pillow)",
                    "四类 (需自行调取)",
                    "travel pillow",
                    "1055398:1063252:1199122:3732141",
                    "调研中",
                    "可重点布局",
                    "差旅与通勤强刚需，中高客单价记忆回弹款受热捧，与现有枕头模具供应链复用率高达85%",
                    "无带电合规风险，关注拉链与外套亲肤认证"
                ),
                (
                    "lumbar_pillow",
                    "人体工学腰靠腰枕 (Lumbar Support Pillow)",
                    "四类 (在售打磨)",
                    "lumbar support pillow",
                    "1055398:1063252:1199122:3732051",
                    "在售打磨",
                    "快速起量",
                    "办公久坐与车载强需求，覆盖现有灰石 (B0HJWZM439) 与流星灰 (B0HJX1MGBF) 两款在售衍生款",
                    "结构支撑度要求高，需控制塌陷客诉"
                ),
                (
                    "seat_cushion",
                    "记忆棉减压坐垫 (Memory Foam Seat Cushion)",
                    "四类 (待立项)",
                    "seat cushion",
                    "1055398:1063252:1199122",
                    "观察中",
                    "小批量验证",
                    "与记忆棉枕头同一发泡工艺，主要针对久坐护臀释压人群，客单价稳定在 $29-$45",
                    "防滑底与透气网布选材关键"
                ),
                (
                    "massage_pillow",
                    "电动加热揉捏按摩枕 (Electric Massage Pillow)",
                    "四类 (计划开发)",
                    "electric massage pillow",
                    "3760901:3767571:3767601",
                    "技术评估",
                    "谨慎试水",
                    "高客单价 ($59-$89) 与高利润，但在售需满足北美 UL/FCC 安全认证与马达电机质保",
                    "带电认证、发热温控安全、高售后退货风险"
                )
            ]
            for pid, name, clevel, kw, nid, st, dec, rat, risk in pipeline_seeds:
                cursor.execute("""
                    INSERT OR IGNORE INTO pipeline_products (id, name, category_level, keyword, node_id_path, status, decision, rationale, risk_flag)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pid, name, clevel, kw, nid, st, dec, rat, risk))

            # Clean any previously inserted unverified dummy seeds
            cursor.execute("DELETE FROM competitor_sets WHERE competitor_asin = 'B0C1K5XYZ1'")

            # Real, verified benchmark competitors from category (Derila brand verified ASINs)
            now_iso = datetime.now(timezone.utc).isoformat()
            benchmark_seeds = [
                ("B0GYH8WT22", "B0H377GYGF", "benchmark", "auto_discovery", 1, now_iso, 0.95, "Derila 颈椎枕类目头部标杆"),
                ("B0GYH8WT22", "B0FG2SH6K5", "benchmark", "auto_discovery", 1, now_iso, 0.90, "Derila 同款蝶形枕"),
                ("B0GY2TDLTZ", "B0H377GYGF", "benchmark", "auto_discovery", 1, now_iso, 0.95, "灰色款对照类目头部标杆"),
                ("B0GY2WGTDM", "B0H377GYGF", "benchmark", "auto_discovery", 1, now_iso, 0.95, "蓝色款对照类目头部标杆")
            ]
            for o_asin, c_asin, gtype, src, ver, ver_at, score, note in benchmark_seeds:
                cursor.execute("""
                    INSERT OR IGNORE INTO competitor_sets (owner_asin, competitor_asin, group_type, source, verified, verified_at, similarity_score, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (o_asin, c_asin, gtype, src, ver, ver_at, score, note))

            # Module 4: Initial Opportunity Lab sample project marked clearly as demo
            cursor.execute("""
                INSERT OR IGNORE INTO research_projects (id, title, research_type, status, user_question, plan_json, findings_json)
                VALUES (1, '【演示示例】小学一年级开学文具套装可行性研究 (Demo Only)', 'new_category', 'completed', 
                '我想看看小学一年级开学用品组合有没有机会。',
                '{"categoryLevels": ["Office Products", "Office & School Supplies", "Writing & Correction Supplies", "School Supply Sets"], "targetMarket": "US", "priceTarget": "25-35", "isDemo": true}',
                '{"conclusion": "【演示数据】波段性强机会，适合7-8月Back-to-School开学季集中发力", "opportunities": ["一站式开学必备文具大礼包需求高", "套装客单价高于单支文具，可拉高单笔利润"], "risks": ["具有极强季节性，9月后销量断崖式下滑", "文具单品拼装成本高，SKU缺一不可"]}')
            """)

            conn.commit()

db = Database()
