from pathlib import Path
from typing import Optional
from sqlmodel import SQLModel, create_engine

# 必须导入 Fact，让它登记到 SQLModel.metadata 里，create_all 才找得到它
from .schema import Fact  # noqa: F401

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class MemoryDB:
    def __init__(self, db_url: Optional[str] = None, echo: bool = False):
        if db_url is None:
            # parents=True 递归创建缺失的父目录，exist_ok=True 目录已存在时不报错
            DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
            # 用 .as_posix() 把 Windows 反斜杠 \ 转成 URL 标准的正斜杠 /
            db_file = (DEFAULT_DATA_DIR / "memory.db").as_posix()
            db_url = f"sqlite:///{db_file}"

        # 只有 SQLite 需要关闭同线程检查；未来换成 MySQL/PG 时传空字典
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

        # 创建全局 Engine（SQLAlchemy 自带连接池和多线程调度）
        self.engine = create_engine(db_url, echo=echo, connect_args=connect_args)
        self.init_db()

    def init_db(self):
        """自动扫描所有 table=True 的模型并建表"""
        SQLModel.metadata.create_all(self.engine)


if __name__ == "__main__":
    # 用纯内存库 + echo=True 试跑，终端能看到自动生成的建表 SQL！
    db = MemoryDB(db_url="sqlite:///:memory:", echo=True)
    print("✅ 第 3 步完成：SQLModel Engine 初始化与自动建表成功！")