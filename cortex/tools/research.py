"""Tools de pesquisa web.

Duas camadas:
  - research.web: busca rapida (uma query, N resultados resumidos).
  - research.deep: busca aprofundada (multiplas queries, fetch de paginas,
    sintese com citacoes via LLM de long_reasoning).

Motor: DuckDuckGo via pacote ddgs. Sem chave, sem cadastro.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from cortex.tools.base import BaseTool, ToolContext, ToolResult


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def _extract_text_from_html(html: str) -> str:
    """Extrai texto legivel de HTML. Simples mas funcional."""
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<nav[^>]*>.*?</nav>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<footer[^>]*>.*?</footer>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<header[^>]*>.*?</header>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def _ddg_search(query: str, max_results: int = 5, region: str = "br-pt") -> list[dict[str, str]]:
    """Busca no DuckDuckGo. Retorna lista de {title, href, body}."""
    try:
        from ddgs import DDGS
    except ImportError:
        raise RuntimeError("ddgs nao instalado. Rode: pip install ddgs")

    results: list[dict[str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region=region, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", ""),
                })
    except Exception as e:
        raise RuntimeError(f"erro na busca: {type(e).__name__}: {e}")
    return results


async def _fetch_url(url: str, timeout: float = 15.0, max_bytes: int = 500_000) -> str:
    """Baixa URL e extrai texto. Retorna string vazia em erro."""
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Cortex/0.2)"},
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            content = r.text[:max_bytes]
            ctype = r.headers.get("content-type", "")
            if "html" in ctype.lower() or content.lstrip().startswith("<"):
                return _extract_text_from_html(content)
            return content
    except Exception:
        return ""


def _fetch_url_sync(url: str, timeout: float = 15.0, max_bytes: int = 500_000) -> str:
    """Versao sincrona de _fetch_url. Usada dentro do research.deep (sync)."""
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Cortex/0.2)"},
        ) as client:
            r = client.get(url)
            r.raise_for_status()
            content = r.text[:max_bytes]
            ctype = r.headers.get("content-type", "")
            if "html" in ctype.lower() or content.lstrip().startswith("<"):
                return _extract_text_from_html(content)
            return content
    except Exception:
        return ""


@dataclass(slots=True)
class ResearchResult:
    query: str
    hits: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None


# ------------------------------------------------------------------
# research.web
# ------------------------------------------------------------------

class ResearchWebTool(BaseTool):
    name = "research.web"
    description = (
        "Busca rapida na web via DuckDuckGo. Retorna titulos, URLs e snippets. "
        "Parametros: query (obrigatorio), max_results (padrao 5, max 20), "
        "region (padrao 'br-pt'; use 'us-en' para resultados em ingles)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5},
            "region": {"type": "string", "default": "br-pt"},
        },
        "required": ["query"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        query = args.get("query", "").strip()
        if not query:
            return ToolResult(ok=False, error="query obrigatoria")

        max_results = min(int(args.get("max_results", 5)), 20)
        region = args.get("region", "br-pt")

        try:
            hits = _ddg_search(query, max_results=max_results, region=region)
        except Exception as e:
            return ToolResult(ok=False, error=str(e))

        if not hits:
            return ToolResult(ok=True, output=f"nenhum resultado para '{query}'")

        lines = [f"resultados para '{query}':"]
        for i, h in enumerate(hits, 1):
            lines.append(f"\n[{i}] {h['title']}")
            lines.append(f"    {h['href']}")
            if h["body"]:
                lines.append(f"    {h['body'][:250]}")

        return ToolResult(
            ok=True,
            output="\n".join(lines),
            meta={"count": len(hits), "query": query, "region": region},
        )


# ------------------------------------------------------------------
# research.fetch - baixa uma URL e retorna o texto
# ------------------------------------------------------------------

class ResearchFetchTool(BaseTool):
    name = "research.fetch"
    description = (
        "Baixa uma URL e extrai o texto legivel. Util para ler uma pagina encontrada "
        "por research.web. Parametro: url (obrigatorio), max_chars (padrao 5000)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "max_chars": {"type": "integer", "default": 5000},
        },
        "required": ["url"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        url = args.get("url", "").strip()
        if not url or not url.startswith(("http://", "https://")):
            return ToolResult(ok=False, error="url http(s) obrigatoria")

        max_chars = int(args.get("max_chars", 5000))

        text = _fetch_url_sync(url)

        if not text:
            return ToolResult(ok=False, error=f"falha ao baixar ou extrair texto de {url}")

        truncated = len(text) > max_chars
        content = text[:max_chars]
        if truncated:
            content += f"\n\n...(truncado em {max_chars} chars de {len(text)})"

        return ToolResult(
            ok=True,
            output=content,
            meta={"url": url, "chars": len(content), "truncated": truncated},
        )


# ------------------------------------------------------------------
# research.deep - multiplas queries + fetch + sintese
# ------------------------------------------------------------------

class ResearchDeepTool(BaseTool):
    name = "research.deep"
    description = (
        "Pesquisa aprofundada. Gera variacoes da query, busca em varias fontes, "
        "baixa as paginas mais relevantes e produz uma sintese. "
        "Parametros: query (obrigatorio), variants (padrao 2), fetch_top (padrao 3), "
        "region (padrao 'br-pt'). ATENCAO: usa LLM remoto, pode ser lento."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "variants": {"type": "integer", "default": 2, "description": "queries adicionais"},
            "fetch_top": {"type": "integer", "default": 3, "description": "quantas paginas baixar"},
            "region": {"type": "string", "default": "br-pt"},
        },
        "required": ["query"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        # research.deep e implementado como tool mas precisa de LLM para gerar
        # variacoes e sintese. Para nao bloquear o loop de tools do planner
        # (que e sync), retornamos uma instrucao ao Cortex para executar em duas
        # etapas via o proprio loop. Alternativa: deixar como assincrono depois.
        #
        # Implementacao atual: gera as variacoes localmente (heuristica simples),
        # busca, faz fetch, concatena. A sintese final fica a cargo do Cortex
        # na resposta final.
        query = args.get("query", "").strip()
        if not query:
            return ToolResult(ok=False, error="query obrigatoria")

        variants = min(int(args.get("variants", 2)), 4)
        fetch_top = min(int(args.get("fetch_top", 3)), 5)
        region = args.get("region", "br-pt")

        # queries: original + variacoes heuristicas
        queries = [query]
        if variants >= 1:
            queries.append(f"{query} estudo")
        if variants >= 2:
            queries.append(f"{query} revisao")
        if variants >= 3:
            queries.append(f"{query} 2025 2026")
        if variants >= 4:
            queries.append(f"{query} pdf")

        all_hits: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for q in queries:
            try:
                hits = _ddg_search(q, max_results=5, region=region)
            except Exception:
                continue
            for h in hits:
                if h["href"] in seen_urls:
                    continue
                seen_urls.add(h["href"])
                all_hits.append(h)

        if not all_hits:
            return ToolResult(ok=False, error=f"nenhum resultado para '{query}'")

        # baixa os top N
        pages: list[tuple[str, str, str]] = []  # (title, url, text)
        for h in all_hits[:fetch_top]:
            text = _fetch_url_sync(h["href"])
            if text:
                pages.append((h["title"], h["href"], text[:8000]))

        # monta o resultado estruturado
        parts = [f"Pesquisa aprofundada: '{query}'", f"Encontrados {len(all_hits)} resultados, {len(pages)} paginas baixadas.", ""]
        parts.append("=== FONTES ===")
        for i, h in enumerate(all_hits[:15], 1):
            parts.append(f"[{i}] {h['title']}")
            parts.append(f"    {h['href']}")
            if h["body"]:
                parts.append(f"    {h['body'][:200]}")

        if pages:
            parts.append("")
            parts.append("=== CONTEUDO DAS PAGINAS ===")
            for i, (title, url, text) in enumerate(pages, 1):
                parts.append(f"\n--- [{i}] {title} ---")
                parts.append(f"URL: {url}")
                parts.append(text[:4000])

        parts.append("")
        parts.append("Instrucao ao Cortex: use as fontes acima para produzir uma sintese "
                     "estruturada com citacoes [N] apontando para as URLs.")

        return ToolResult(
            ok=True,
            output="\n".join(parts),
            meta={
                "query": query,
                "total_hits": len(all_hits),
                "pages_fetched": len(pages),
                "queries_used": len(queries),
            },
        )
