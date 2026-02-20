import os
import sqlite3
import struct
import time
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
vec_dll_path = os.path.join(script_dir, "vec0.dll")

def serialize_f32(vector: list[float]) -> bytes:
    """将浮点数列表序列化为紧凑的二进制格式"""
    return struct.pack("%sf" % len(vector), *vector)

# 初始化数据库并加载扩展
# db = sqlite3.connect(":memory:")
db = sqlite3.connect("vectors.db")
db.enable_load_extension(True)
db.load_extension(vec_dll_path)
db.enable_load_extension(False)

# 创建 vec0 虚拟表（4维 float32 向量）
db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS vec_items USING vec0(embedding float[384]);")

N = 100000

input("请查看插入前内存")

with db:
    for i in range(N):
        db.execute(
            "INSERT INTO vec_items(rowid, embedding) VALUES (?, ?)",
            [i, serialize_f32(np.random.randn(384))],
        )

input("请查看插入后内存")

# KNN 查询：找到最近的 3 个向量
start = time.time()
query = np.random.randn(384)
rows = db.execute("""
    SELECT rowid, distance
    FROM vec_items
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 3
""", [serialize_f32(query)]).fetchall()
print(f"耗时：{time.time()-start}")

for row_id, dist in rows: print(f"rowid={row_id}, distance={dist}")




