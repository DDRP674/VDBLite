import time
import numpy as np
from tokenizers import Tokenizer as HFTokenizer
import onnxruntime as ort

class Embedder:
    def __init__(self,
                 onnx_path: str = "./model/model-int8.onnx",
                 tokenizer: str = "./model/tokenizer.json",
                 model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 providers=None,
                 max_length: int = 128):
        self.lock = None
        self.onnx_path = onnx_path
        self.max_length = max_length
        self._use_fast = False
        tok = HFTokenizer.from_file(tokenizer)
        tok.enable_truncation(self.max_length)
        tok.enable_padding(length=self.max_length)
        self.tokenizer = tok
        self._use_fast = True
        providers = providers or ["CPUExecutionProvider"]
        self.sess = ort.InferenceSession(self.onnx_path, providers=providers)
        # warm-up to get shape
        self.shape = self.embed([""]).shape

    def get_shape(self) -> tuple: return self.shape

    def embed(self, texts: list[str] | str) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        if self._use_fast:
            encs = self.tokenizer.encode_batch(texts)
            input_ids = np.array([enc.ids for enc in encs], dtype=np.int64)
            attention_mask = np.array([enc.attention_mask for enc in encs], dtype=np.int64)
            inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
        else:
            enc = self.tokenizer(texts, padding=True, truncation=True,
                                 max_length=self.max_length, return_tensors="np")
            inputs = {
                "input_ids": enc["input_ids"].astype(np.int64),
                "attention_mask": enc["attention_mask"].astype(np.int64),
            }
        outs = self.sess.run(None, inputs)
        emb = outs[0]
        # ensure L2-normalized (ONNX export may already normalize)
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms = np.clip(norms, 1e-9, None)
        emb = emb / norms
        return emb.flatten()


if __name__ == "__main__":
    start = time.time()
    e = Embedder()
    print(f"加载时间：{time.time()-start}")
    start = time.time()
    a = e.embed(["今天天气很好"])
    b = e.embed(["The weather is good today."])
    c = e.embed(["今日は天気が良いです"])
    d = e.embed(["我爱吃苹果"])
    print(f"推理时间：{time.time()-start}")
    print(a@b)
    print(a@c)
    print(a@d)
    print(b@d)
    print(c@d)
