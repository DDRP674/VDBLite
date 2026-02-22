import json, queue, uuid
import subprocess
import threading
import time

def stdout_decode(message: str) -> dict: 
    """解析子进程输出，如果并非输出则输出空字典"""
    if message.startswith("#STDOUT#") and message.endswith("#STDOUT#"): return json.loads(message[8:-8])
    return {}

def stdin_input(json_obj: dict) -> str: return json.dumps(json_obj).replace("\n", "")+"\n"

process = subprocess.Popen(
    ["python", "./server_lib.py"],
    stdin=subprocess.PIPE,  # 给exe开一个"输入管道"
    stdout=subprocess.PIPE, # 给exe开一个"输出管道"
    stderr=subprocess.PIPE,  # 捕获子进程的错误输出（关键）
    universal_newlines=True  
)

output_queue = queue.Queue()

def output_thread():
    while True:
        output = process.stdout.readline().strip()
        output_dict = stdout_decode(output)
        if output_dict: output_queue.put(output_dict)

threading.Thread(target=output_thread, daemon=True).start()

a = "今天天气很好"
b = "The weather is good today."
c = "今日は天気が良いです"
d = "我爱吃苹果"

cmds = [
    ("get_size", {}),
    ("search", {"text": d, "k": 5, "threshold": 0.0}),
    ("get_text_by_id", {"id": 2}),
    ("get_id_by_text", {"text": a}),
    ("reduce", {"n": 1}),
    ("delete", {"id": 2}),
    ("update", {"id": 3, "text": "yeah"}),
    ("stop", {})
]

while True:
    output = output_queue.get()
    if output == {"signal": "ready"}: break

start = time.time()
for i in range(1000):
    process.stdin.write(stdin_input({"func_name": "insert_with_reduce_without_repeat", "kwargs": {"text": str(uuid.uuid4())}})) 
    process.stdin.flush()
    output = output_queue.get()

print(f"插入耗时：{time.time()-start}")

for func_name, kwargs in cmds:
    print(func_name, kwargs)
    start = time.time()
    process.stdin.write(stdin_input({"func_name": func_name, "kwargs": kwargs}))
    process.stdin.flush()  # 强制写入，不缓存

    output = output_queue.get()
    if output: print(f"子进程输出：{output}")
    print(f"耗时：{time.time()-start}")
    # process.stdout.flush()

    