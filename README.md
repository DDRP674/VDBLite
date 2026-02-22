This is just a light-weighted vector database, made by SQLite-vec.  
  
It uses "paraphrase-multilingual-MiniLM-L12-v2" in ONNX format, int8, for embedding.  
  
This repo is for my own use.

Usage:  
All outputs has #STDOUT# on both sides.  

Ready signal: {"signal": "ready"}  
Exit signal: {"signal": "exit"}  

Input format:  
{"func_name": "insert", "kwargs": {"text": ""}}  
{"func_name": "insert_with_reduce", "kwargs": {"text": ""}}  
{"func_name": "insert_with_reduce_without_repeat", "kwargs": {"text": ""}}  
{"func_name": "search", "kwargs": {"text": "", "k": int, "threshold": 0.0}}  
{"func_name": "get_size"}  
{"func_name": "get_text_by_id", "kwargs": {"id": int}}  
{"func_name": "get_id_by_text", "kwargs": {"text": ""}}  
{"func_name": "delete", "kwargs": {"id": int}}  
{"func_name": "update", "kwargs": {"id": int, "text": ""}}  
{"func_name": "stop"}  

Output format:  
{"func_name": "search", "result": [{"content": "", "similarity": float, "id": int}]}  
{"func_name": "get_size", "result": int}  
{"func_name": "get_text_by_id", "result": "content"}  
{"func_name": "get_id_by_text", "result": id}  
{"func_name": "delete", "result": "ok"}  
{"func_name": "update", "result": "ok"}  

Error format: {"status": "error", "info": str}  