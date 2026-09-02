"""Local retrieval layer for the bundled knowledge base (offline RAG)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


class LocalKnowledgeBase:
    """Small dependency-free retriever; embeddings can replace it later transparently."""

    def __init__(self, config: Dict[str, Any]):
        self.root = Path(config.get("memory", {}).get("knowledge_base_path", "knowledge_base")).resolve()

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        terms = set(re.findall(r"[\wáàâãéêíóôõúç]{3,}", query.lower()))
        if not terms or not self.root.exists():
            return []
        matches = []
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt"}:
                continue
            try:
                raw = path.read_text(encoding="utf-8", errors="replace")
                text = json.dumps(json.loads(raw), ensure_ascii=False) if path.suffix.lower() == ".json" else raw
                # File and directory names are useful local metadata too (e.g. a
                # Portuguese query can find an English-keyed JSON document).
                text = f"{path.stem} {path.parent.name}\n{text}"
            except (OSError, json.JSONDecodeError):
                continue
            lower = text.lower()
            score = sum(lower.count(term) for term in terms)
            if score:
                position = min((lower.find(term) for term in terms if term in lower), default=0)
                snippet = " ".join(text[max(0, position - 180):position + 500].split())
                matches.append({"source": str(path), "score": score, "snippet": snippet})
        return sorted(matches, key=lambda item: item["score"], reverse=True)[:max(1, min(limit, 20))]
