import json, queue, threading
from VectorDatabase import VectorDatabase
import sys

# 务必严格检查所有通路都使用json_obj_output输出，否则子进程卡死

def json_obj_output(json_object: dict):
    json_str = json.dumps(json_object).replace("\n", "")
    print(f"#STDOUT#{json_str}#STDOUT#"+"\n")
    sys.stdout.flush()
    
class server:
    def __init__(self, database_name="vdb.db", max_size=10000):
        self.running = False
        self.input_queue = queue.Queue()
        self.vdb = VectorDatabase(database_name, max_size)
        json_obj_output({"signal": "ready"})

    def run(self): 
        self.running = True
        threading.Thread(target=self.input_thread, daemon=True).start()
        self.processing()

    def processing(self):
        while self.running:
            try:
                cmd = self.input_queue.get()

                if not cmd.get("func_name", False): 
                    json_obj_output({"status": "error", "info": "No function specified"})
                    continue

                if cmd["func_name"] == "insert":
                    text = cmd.get("kwargs", {}).get("text", "").strip()
                    if text: self.vdb.insert(text)
                    json_obj_output({"func_name": "insert", "result": "ok"})
                    continue

                if cmd["func_name"] == "insert_with_reduce": 
                    text = cmd.get("kwargs", {}).get("text", "").strip()
                    if text: 
                        self.vdb.insert(text)
                        self.vdb.reduce(self.vdb.get_size()-self.vdb.maxsize)
                    json_obj_output({"func_name": "insert_with_reduce", "result": "ok"})
                    continue

                if cmd["func_name"] == "insert_with_reduce_without_repeat":
                    text = cmd.get("kwargs", {}).get("text", "").strip()
                    if text: 
                        if self.vdb.get_id_by_text(text) == -1: 
                            self.vdb.insert(text)
                            self.vdb.reduce(self.vdb.get_size()-self.vdb.maxsize)
                    json_obj_output({"func_name": "insert_with_reduce_without_repeat", "result": "ok"})
                    continue

                if cmd["func_name"] == "reduce":
                    n = cmd.get("kwargs", {}).get("n", 0)
                    self.vdb.reduce(n)
                    json_obj_output({"func_name": "reduce", "result": "ok"})
                    continue

                if cmd["func_name"] == "search":
                    kwargs = cmd.get("kwargs", {})
                    text = kwargs.get("text", "").strip()
                    k = kwargs.get("k", 5)
                    threshold = kwargs.get("threshold", 0.0)
                    res = self.vdb.search(text, k, threshold)
                    json_obj_output({"func_name": "search", "result": res})
                    continue

                if cmd["func_name"] == "get_size":
                    json_obj_output({"func_name": "get_size", "result": self.vdb.get_size()})
                    continue

                if cmd["func_name"] == "get_text_by_id":
                    kwargs = cmd.get("kwargs", {})
                    id_val = kwargs.get("id", None)
                    try: id_int = int(id_val)
                    except (TypeError, ValueError):
                        json_obj_output({"status": "error", "info": "Invalid id"})
                        continue
                    try:
                        text = self.vdb.get_text_by_id(id_int)
                        json_obj_output({"func_name": "get_text_by_id", "result": text})
                    except Exception as e: json_obj_output({"status": "error", "info": str(e)})
                    continue
                
                if cmd["func_name"] == "get_id_by_text":
                    kwargs = cmd.get("kwargs", {})
                    text = kwargs.get("text", "").strip()
                    if not text:
                        json_obj_output({"status": "error", "info": "Text is empty"})
                        continue
                    try:
                        id_val = self.vdb.get_id_by_text(text)
                        json_obj_output({"func_name": "get_id_by_text", "result": id_val})
                    except Exception as e: json_obj_output({"status": "error", "info": str(e)})
                    continue
                
                if cmd["func_name"] == "delete":
                    kwargs = cmd.get("kwargs", {})
                    id_val = kwargs.get("id", None)
                    try: id_int = int(id_val)
                    except (TypeError, ValueError):
                        json_obj_output({"status": "error", "info": "Invalid id"})
                        continue
                    try:
                        self.vdb.delete(id_int)
                        json_obj_output({"func_name": "delete", "result": "ok"})
                    except Exception as e: json_obj_output({"status": "error", "info": str(e)})
                    continue
                
                if cmd["func_name"] == "update":
                    kwargs = cmd.get("kwargs", {})
                    id_val = kwargs.get("id", None)
                    text = kwargs.get("text", "").strip()
                    try: id_int = int(id_val)
                    except (TypeError, ValueError): 
                        json_obj_output({"status": "error", "info": "Invalid id"})
                        continue
                    try:
                        self.vdb.update(id_int, text)
                        json_obj_output({"func_name": "update", "result": "ok"})
                    except Exception as e: json_obj_output({"status": "error", "info": str(e)})
                    continue

                if cmd["func_name"] == "stop": 
                    self.vdb.stop() 
                    self.stop()
                    json_obj_output({"signal": "exit"})
                    continue

                else:
                    json_obj_output({"status": "error", "info": "Unknown function: "+cmd["func_name"]})
                    continue

            except Exception as e: json_obj_output({"status": "error", "info": str(e)})

    def stop(self): self.running = False

    # 线程

    def input_thread(self):
        while self.running:
            input_line = sys.stdin.readline().strip()
            try: cmd = json.loads(input_line)
            except json.JSONDecodeError as e: 
                json_obj_output({"status": "error", "info": str(e)})
                continue
            self.input_queue.put(cmd)

if __name__ == "__main__":
    s = server()
    s.run()