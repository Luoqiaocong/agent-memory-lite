import sqlite3
from pathlib import Path
import threading

db_path = Path(__file__).resolve().parent.parent.parent/ "data" / "memory.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

class MemoryDB:
    def __init__(self, db_path=db_path):
        self.db_path = db_path
        # 1. 创建一个线程隔离的“魔法储物柜”
        self._local = threading.local()
        self._init_table()
        
    @property
    def conn(self) -> sqlite3.Connection:
        # 2. 去当前线程的抽屉里看看有没有专属连接（第一次来会没有，所以用 getattr 防报错）
        conn = getattr(self._local, "conn", None)
        
        if conn is None:
            # 3. 如果当前线程还没有连接，就现场为它单独建一根！
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            # 开启 WAL 模式：允许不同线程“边读边写”，防 database is locked
            conn.execute("PRAGMA journal_mode=WAL;")
            # 存进当前线程自己的抽屉里，下次直接复用
            self._local.conn = conn
            
        return conn

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