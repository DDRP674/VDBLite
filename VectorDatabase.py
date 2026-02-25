from onnx_embedder import Embedder
import threading, os, struct, sqlite3

def serialize_f32(vector: list[float]) -> bytes:
    """将浮点数列表序列化为紧凑的二进制格式"""
    return struct.pack("%sf" % len(vector), *vector)

# 使用余弦相似度。id使用整数，其数值大小代表插入的早晚
# 这个并非HNSW，而是全遍历的实现

class VectorDatabase:
    def __init__(self, database_name="vectors.db", maxsize=10000):
        self.lock = threading.Lock()
        self.maxsize = maxsize

        # Sqlite-vec Initialization
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vec_dll_path = os.path.join(script_dir, "vec0.dll")

        self.db = sqlite3.connect(database_name, check_same_thread=False)
        self.db.enable_load_extension(True)
        self.db.load_extension(vec_dll_path)
        self.db.enable_load_extension(False)

        self.running = True

        # Embedding Initialization
        self.embedder = Embedder()
        self.dim = self.embedder.get_shape()[0]

        # 创建表
        with self.lock:
            cur = self.db.cursor()
            cur.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_data USING vec0(
                    embedding FLOAT[{self.dim}] distance_metric=cosine
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS text_data (
                    id INTEGER PRIMARY KEY,
                    content TEXT
                );
            """)
            # 为content字段添加索引，提高按内容查找的效率
            cur.execute("CREATE INDEX IF NOT EXISTS idx_text_data_content ON text_data(content);")
            self.db.commit()

    def insert(self, text: str) -> None:
        """插入记忆"""
        vec = self.embedder.embed(text)
        vec_json = str(list(map(float, vec)))
        with self.lock:
            cur = self.db.cursor()
            # 插入向量，rowid自增
            cur.execute("INSERT INTO vec_data(embedding) VALUES (?)", (vec_json,))
            rowid = cur.lastrowid
            cur.execute("INSERT INTO text_data(id, content) VALUES (?, ?)", (rowid, text))
            self.db.commit()

    def get_size(self) -> int:
        """获取数据库当前数据条数"""
        with self.lock:
            cur = self.db.cursor()
            cur.execute("SELECT COUNT(*) FROM vec_data")
            return cur.fetchone()[0]

    def reduce(self, n: int) -> None:
        """删去最早的n个数据。n小于等于0则无操作。"""
        if n <= 0: return
        with self.lock:
            cur = self.db.cursor()
            cur.execute(f"SELECT rowid FROM vec_data ORDER BY rowid ASC LIMIT ?", (n,))
            ids = [row[0] for row in cur.fetchall()]
            if ids:
                cur.executemany("DELETE FROM vec_data WHERE rowid=?", [(i,) for i in ids])
                cur.executemany("DELETE FROM text_data WHERE id=?", [(i,) for i in ids])
                self.db.commit()

    def search(self, text: str, k=5, threshold=0.0) -> list[dict]:
        """查找相似度大于threshold的k最近邻。返回格式：\n
        [{"content": "", "similarity": float, "id": int}]"""
        vec = self.embedder.embed(text)
        vec_json = str(list(map(float, vec)))
        with self.lock:
            cur = self.db.cursor()
            cur.execute(f"""
                SELECT rowid, distance FROM vec_data
                WHERE embedding MATCH ?
                ORDER BY distance ASC
                LIMIT ?
            """, (vec_json, k))
            results = cur.fetchall()
            out = []
            for rowid, dist in results:
                similarity = 1-dist
                if similarity < threshold: continue
                cur.execute("SELECT content FROM text_data WHERE id=?", (rowid,))
                row = cur.fetchone()
                content = row[0] if row else ""
                out.append({"content": content, "similarity": similarity, "id": rowid})
            return out
        
    def delete(self, id: int) -> None:
        """删除对应id的数据"""
        with self.lock:
            cur = self.db.cursor()
            cur.execute("DELETE FROM vec_data WHERE rowid=?", (id,))
            cur.execute("DELETE FROM text_data WHERE id=?", (id,))
            self.db.commit()

    def update(self, id: int, text: str) -> None:
        """将对应id的数据改为新的数据"""
        vec = self.embedder.embed(text)
        vec_json = str(list(map(float, vec)))
        with self.lock:
            cur = self.db.cursor()
            cur.execute("UPDATE vec_data SET embedding=? WHERE rowid=?", (vec_json, id))
            cur.execute("UPDATE text_data SET content=? WHERE id=?", (text, id))
            self.db.commit()

    def get_id_by_text(self, text: str) -> int:
        """根据文本获取对应id。如果不存在则返回-1"""
        with self.lock:
            cur = self.db.cursor()
            cur.execute("SELECT id FROM text_data WHERE content=?", (text,))
            row = cur.fetchone()
            return row[0] if row else -1

    def get_text_by_id(self, id: int) -> str:
        """根据id获取文本，如果不存在则返回空字符串"""
        with self.lock:
            cur = self.db.cursor()
            cur.execute("SELECT content FROM text_data WHERE id=?", (id,))
            row = cur.fetchone()
            return row[0] if row else ""

    def stop(self): 
        self.db.close()
        self.running = False

if __name__ == "__main__":
    vdb = VectorDatabase()
    import time
    # N = int(input("输入测试数量：").strip())

    # start = time.time()
    # for i in range(N): vdb.insert(str(i))
    # print(f"插入用时：{time.time()-start}")
    
    start = time.time()
    print(vdb.get_size())
    print(f"获取总量用时：{time.time()-start}")

    start = time.time()
    vdb.search("sb")
    print(f"查询用时：{time.time()-start}")

    start = time.time()
    vdb.reduce(1)
    print(f"削减用时：{time.time()-start}")

    start = time.time()
    vdb.delete(2)
    print(f"删除用时：{time.time()-start}")

    start = time.time()
    vdb.update(3, "a")
    print(f"修改用时：{time.time()-start}")

    start = time.time()
    print(vdb.get_id_by_text("6"))
    print(f"id获取用时：{time.time()-start}")

    start = time.time()
    print(vdb.get_text_by_id(6))
    print(f"文本获取用时：{time.time()-start}")