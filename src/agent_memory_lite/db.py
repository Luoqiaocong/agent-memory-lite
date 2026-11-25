import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent.parent/ "data" / "memory.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

class MemoryDB:
    def __init__(self, db_path=db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_table()

    def _init_table(self):
        """第 1 步：建库建表"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,              -- 谁的记忆
                    fact_key TEXT NOT NULL,             -- 哪一类，如 preference
                    fact_value TEXT NOT NULL,           -- 具体值，如 摄影
                    confidence REAL DEFAULT 1.0,        -- 置信度，0到1
                    hit_count INTEGER DEFAULT 1,        -- 被提及/提取次数
                    is_active INTEGER DEFAULT 1,        -- 是否启用(1启用, 0失效)
                    previous_value TEXT,                -- 被覆盖前的旧值，可空
                    updated_at REAL NOT NULL,           -- 更新时间
                    
                    -- 核心约束：同一个用户的同一条具体事实不可重复
                    UNIQUE(user_id, fact_key, fact_value)
                );
            """)

# 测试运行
if __name__ == "__main__":
    db = MemoryDB()
    db._init_table()
    print("✅ 第 1 步完成：专业级记忆事实表初始化成功！")