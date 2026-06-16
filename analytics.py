import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict

DB_PATH = "bot_analytics.db"


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            analysis_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'success'
        )
    """)
    
    conn.commit()
    conn.close()


def log_analysis(user_id: int, username: str = None, analysis_type: str = "screenshot"):
    """Логировать анализ"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO analyses (user_id, username, analysis_type, timestamp, status)
        VALUES (?, ?, ?, ?, 'success')
    """, (user_id, username, analysis_type, datetime.now()))
    
    conn.commit()
    conn.close()


def get_stats_today() -> Dict:
    """Статистика за сегодня"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    cursor.execute("""
        SELECT user_id, username, analysis_type, COUNT(*) as count
        FROM analyses
        WHERE DATE(timestamp) = ?
        GROUP BY user_id, analysis_type
        ORDER BY user_id, count DESC
    """, (today,))
    
    rows = cursor.fetchall()
    conn.close()
    
    stats = {}
    for user_id, username, analysis_type, count in rows:
        if user_id not in stats:
            stats[user_id] = {"username": username, "total": 0, "by_type": {}}
        stats[user_id]["total"] += count
        stats[user_id]["by_type"][analysis_type] = count
    
    return stats


def get_stats_week() -> Dict:
    """Статистика за неделю"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    week_ago = (datetime.now() - timedelta(days=7)).date()
    
    cursor.execute("""
        SELECT user_id, username, COUNT(*) as count
        FROM analyses
        WHERE DATE(timestamp) >= ?
        GROUP BY user_id
        ORDER BY count DESC
    """, (week_ago,))
    
    rows = cursor.fetchall()
    conn.close()
    
    stats = {}
    for user_id, username, count in rows:
        stats[user_id] = {"username": username, "count": count}
    
    return stats


def get_total_stats() -> Dict:
    """Общая статистика"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as unique_users,
               COUNT(*) as total_analyses
        FROM analyses
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        "unique_users": result[0] or 0,
        "total_analyses": result[1] or 0
    }


def format_stats_message() -> str:
    """Форматировать статистику в сообщение"""
    today_stats = get_stats_today()
    week_stats = get_stats_week()
    total_stats = get_total_stats()
    
    message = "📊 <b>СТАТИСТИКА АНАЛИЗОВ</b>\n\n"
    
    # За сегодня
    if today_stats:
        message += "📅 <b>За сегодня:</b>\n"
        for user_id in sorted(today_stats.keys()):
            data = today_stats[user_id]
            username = data["username"] or f"User_{user_id}"
            total = data["total"]
            by_type = data["by_type"]
            
            types_str = ", ".join([f"{k}: {v}" for k, v in by_type.items()])
            message += f"  • <code>{username}</code> (ID: {user_id}): {total} анализов ({types_str})\n"
    else:
        message += "📅 <b>За сегодня:</b>\n  Анализов нет\n"
    
    message += "\n"
    
    # За неделю
    if week_stats:
        message += "📈 <b>За неделю (последние 7 дней):</b>\n"
        for user_id in sorted(week_stats.keys()):
            data = week_stats[user_id]
            username = data["username"] or f"User_{user_id}"
            count = data["count"]
            message += f"  • <code>{username}</code>: {count} анализов\n"
    else:
        message += "📈 <b>За неделю:</b>\n  Анализов нет\n"
    
    message += "\n"
    
    # Всего
    message += f"📊 <b>Всего:</b>\n"
    message += f"  • Менеджеров: {total_stats['unique_users']}\n"
    message += f"  • Анализов: {total_stats['total_analyses']}\n"
    
    return message


# Инициализируем БД при импорте
if not os.path.exists(DB_PATH):
    init_db()
