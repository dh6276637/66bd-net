#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复错误分类的汽车文章"""
import MySQLdb
from MySQLdb.cursors import DictCursor

DB_CONFIG = {
    "host": "localhost",
    "user": "paper_user",
    "passwd": "paper_db2026",
    "db": "dongshushu_paper",
    "charset": "utf8mb4"
}

# 汽车相关关键词
CAR_KEYWORDS = [
    "汽车", "电动车", "新能源", "智驾", "自动驾驶", "车企",
    "比亚迪", "特斯拉", "蔚来", "理想", "小鹏", "吉利", "长安",
    "小米汽车", "SU7", "YU7", "GT", "SUV", "轿车", "跑车", "MPV",
    "续航", "充电", "电池", "辅助驾驶", "Cybertruck"
]

def fix_car_category():
    conn = MySQLdb.connect(**DB_CONFIG)
    cur = conn.cursor(DictCursor)
    try:
        # 找出错误分类的汽车文章
        car_keyword_condition = " OR ".join([
            f"(title LIKE '%{kw}%' OR content LIKE '%{kw}%')" 
            for kw in CAR_KEYWORDS
        ])
        
        # 找出被错误归类到数码硬件的汽车文章
        cur.execute(f"""
            SELECT id, title, category 
            FROM article 
            WHERE category = '数码硬件' 
              AND ({car_keyword_condition})
              AND is_published = 1
            ORDER BY created_at DESC
        """)
        articles = cur.fetchall()
        
        if articles:
            print(f"找到 {len(articles)} 篇被错误分类的汽车文章：")
            for art in articles[:10]:  # 只显示前10条
                print(f"  - {art['title']} (ID: {art['id']})")
            
            # 更新分类
            update_sql = f"""
                UPDATE article 
                SET category = '汽车' 
                WHERE category = '数码硬件' 
                  AND ({car_keyword_condition})
                  AND is_published = 1
            """
            cur.execute(update_sql)
            updated_count = cur.rowcount
            conn.commit()
            print(f"\n成功更新了 {updated_count} 篇文章的分类！")
        else:
            print("没有找到需要修复的文章")
            
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    fix_car_category()
