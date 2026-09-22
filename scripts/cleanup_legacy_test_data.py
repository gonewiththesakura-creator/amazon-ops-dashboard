import os
import sys
import shutil
import sqlite3
from datetime import datetime

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "backend", "v2_store.db")
    
    if not os.path.exists(db_path):
        print(f"[CLEANUP] Database not found at {db_path}. Skipping.")
        return

    # 1. Automatic Timestamped Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(project_root, "backend", f"v2_store_backup_{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    print(f"[CLEANUP] Created database backup at: {backup_path}")

    # 2. Inspect and Clean Legacy Test Data
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Pre-clean counts
    c.execute("SELECT COUNT(*) FROM pipeline_products")
    pre_pipeline = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM competitor_sets")
    pre_competitors = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM research_projects")
    pre_research = c.fetchone()[0]

    # Clean test_knee_pillow from pipeline_products (prevent node pollution)
    c.execute("DELETE FROM pipeline_products WHERE id = 'test_knee_pillow'")
    deleted_pipeline = c.rowcount

    # Clean fake/test competitor entries
    c.execute("""
        DELETE FROM competitor_sets 
        WHERE notes LIKE '%单元测试%' 
           OR notes LIKE '%test%' 
           OR competitor_asin LIKE 'B0TEST%' 
           OR competitor_asin LIKE 'B0FAKE%'
    """)
    deleted_competitors = c.rowcount

    # Clean dummy research projects with fake keywords like qwertyxyz
    c.execute("""
        DELETE FROM research_projects 
        WHERE title LIKE '%qwertyxyz%' 
           OR title LIKE '%单元测试%'
           OR user_question LIKE '%qwertyxyz%'
    """)
    deleted_research = c.rowcount

    conn.commit()

    # Post-clean counts
    c.execute("SELECT COUNT(*) FROM pipeline_products")
    post_pipeline = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM competitor_sets")
    post_competitors = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM research_projects")
    post_research = c.fetchone()[0]
    conn.close()

    print("[CLEANUP SUMMARY]")
    print(f"  pipeline_products: {pre_pipeline} -> {post_pipeline} (Removed {deleted_pipeline})")
    print(f"  competitor_sets:   {pre_competitors} -> {post_competitors} (Removed {deleted_competitors})")
    print(f"  research_projects: {pre_research} -> {post_research} (Removed {deleted_research})")
    print("[CLEANUP] Legacy test pollution successfully cleaned from production store.")

if __name__ == "__main__":
    main()
