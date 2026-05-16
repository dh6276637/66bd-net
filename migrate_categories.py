#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新文章分类：把 '开发者' 改成 '开发者生态'"""
import MySQLdb
from MySQLdb.cursors import DictCursor

DB_CONFIG = {
    "host": "localhost",
    "user": "paper_user",
    "passwd": "paper_db2026",
    "db": "dongshushu_paper",
    "charset": "utf8mb4"
}

def migrate_categories():
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor(DictCursor)
    try:
        # 更新分类
        cur.execute("UPDATE article SET category = '开发者生态' WHERE category = '开发者'")
        updated_count = cur.rowcount
        conn.commit()
        print(f"成功更新了 {updated_count} 篇文章的分类！")
        
        # 检查现在所有的分类
        cur.execute("SELECT DISTINCT category FROM article ORDER BY category")
        categories = cur.fetchall()
        print("\n当前数据库中的分类：")
        for cat in categories:
            cur.execute("SELECT COUNT(*) as count FROM article WHERE category = %s", (cat['category'],))
            count = cur.fetchone()['count']
            print(f"  - {cat['category']}: {count} 篇文章")
            
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    migrate_categories()
