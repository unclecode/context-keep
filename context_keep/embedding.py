"""Embedding score: how much a message reads like the start of new work.

A small local model (MiniLM, ONNX, CPU) turns each user message into a
vector. The message is scored against two curated prototype lists in
prototypes.json: sentences that start a work unit (positive) and sentences
from inside a unit (negative).

score = best cosine similarity to a positive prototype
         - best cosine similarity to a negative prototype

Range is about -0.5 to +0.5. Positive = reads like a topic start.
"""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
MODEL_PATH = ROOT / "models" / "minilm" / "model.onnx"
TOKENIZER_PATH = ROOT / "models" / "minilm" / "tokenizer.json"
PROTOTYPES_PATH = ROOT / "prototypes.json"

MAX_CHARS = 200   # a topic turn shows in the first words of a message
MAX_TOKENS = 64

_session = None
_tokenizer = None


def _load():
    global _session, _tokenizer
    if _session is None:
        import onnxruntime
        from tokenizers import Tokenizer
        _session = onnxruntime.InferenceSession(
            str(MODEL_PATH), providers=["CPUExecutionProvider"])
        _tokenizer = Tokenizer.from_file(str(TOKENIZER_PATH))
        _tokenizer.enable_truncation(max_length=MAX_TOKENS)
        _tokenizer.enable_padding()
    return _session, _tokenizer


_cache = {}


def embed(texts):
    """Return one L2-normalized vector per text (mean pooling over tokens).

    Vectors are cached per text, so scoring the same window again is free.
    """
    clipped = [t[:MAX_CHARS] for t in texts]
    missing = [t for t in dict.fromkeys(clipped) if t not in _cache]
    if missing:
        for text, vec in zip(missing, _embed_batch(missing)):
            _cache[text] = vec
    return np.stack([_cache[t] for t in clipped])


def _embed_batch(texts):
    session, tokenizer = _load()
    encoded = tokenizer.encode_batch(list(texts))
    ids = np.array([e.ids for e in encoded], dtype=np.int64)
    mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
    out = session.run(None, {
        "input_ids": ids,
        "attention_mask": mask,
        "token_type_ids": np.zeros_like(ids),
    })[0]                                   # (batch, tokens, 384)
    m = mask[:, :, None].astype(np.float32)
    vecs = (out * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
    return vecs / np.clip(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9, None)


def topic_start_scores(texts):
    """Topic-start score per text; see the module doc for the definition."""
    protos = json.loads(PROTOTYPES_PATH.read_text())
    pos = embed(protos["positive"])
    neg = embed(protos["negative"])
    batch = embed(texts)
    return (batch @ pos.T).max(axis=1) - (batch @ neg.T).max(axis=1)
