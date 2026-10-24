#!/usr/bin/env python3
"""
sources_manager.py - Gestor determinista de fuentes para Searcher Floydia.
Maneja normalización de URLs, deduplicación por SHA256, categorización de autoridad
y generación del índice de fuentes en Markdown.
"""

import sys
import os
import json
import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from datetime import datetime, timezone

TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'fbclid', 'ref', 'source', 'token', 'auth'
}

def clean_url(raw_url: str) -> str:
    """Elimina parámetros de tracking y normaliza la URL."""
    try:
        parsed = urlparse(raw_url.strip())
        query_params = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_params = [
            (k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS
        ]
        new_query = urlencode(filtered_params)
        # Normalizar sin slash final innecesario en la ruta
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        clean = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            new_query,
            '' # eliminar fragmentos #
        ))
        return clean
    except Exception:
        return raw_url.strip()

def compute_hash(text: str) -> str:
    """Calcula el hash SHA256 de un texto normalizado."""
    norm_text = re.sub(r'\s+', ' ', text.strip()).encode('utf-8')
    return hashlib.sha256(norm_text).hexdigest()[:16]

class SourcesManager:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.fuentes_jsonl = os.path.join(workspace_dir, "02_fuentes", "fuentes.jsonl")
        self.indice_md = os.path.join(workspace_dir, "indice_fuentes.md")
        os.makedirs(os.path.dirname(self.fuentes_jsonl), exist_ok=True)
        self.sources = self._load_sources()

    def _load_sources(self):
        sources = []
        if os.path.exists(self.fuentes_jsonl):
            with open(self.fuentes_jsonl, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            sources.append(json.loads(line))
                        except Exception:
                            pass
        return sources

    def add_source(self, url: str, titulo: str, tipo: str, canal: str, autoridad: int = 3, raw_content: str = "", subpreguntas: list = None):
        """Añade una fuente asegurando deduplicación por URL y hash."""
        url_canonica = clean_url(url)
        content_hash = compute_hash(raw_content) if raw_content else compute_hash(url_canonica)

        # Chequear duplicados
        for s in self.sources:
            if s.get("url_canonica") == url_canonica or (s.get("hash") == content_hash and content_hash != ""):
                print(f"[DEDUP] Fuente duplicada omitida: {url_canonica} (ID existente: {s.get('id')})")
                return s

        nuevo_id = f"F{len(self.sources) + 1:03d}"
        now_iso = datetime.now(timezone.utc).isoformat()

        source_entry = {
            "id": nuevo_id,
            "url": url,
            "url_canonica": url_canonica,
            "titulo": titulo or "Sin título",
            "tipo": tipo, # web, paper, video, repo, social, doc
            "canal": canal, # grounding, last30days, playwright, perplexity, manual
            "autoridad": max(1, min(5, autoridad)),
            "subpreguntas": subpreguntas or [],
            "hash": content_hash,
            "created_at": now_iso,
            "en_cuaderno": False
        }

        self.sources.append(source_entry)
        with open(self.fuentes_jsonl, 'a', encoding='utf-8') as f:
            f.write(json.dumps(source_entry, ensure_ascii=False) + "\n")

        print(f"[OK] Fuente registrada [{nuevo_id}] (Nivel {autoridad}): {titulo} -> {url_canonica}")
        return source_entry

    def generate_index_markdown(self):
        """Genera el archivo indice_fuentes.md ordenado por autoridad e ID."""
        if not self.sources:
            return

        lines = [
            "# Índice de Fuentes y Auditoría de Evidencia\n",
            f"> Total de fuentes registradas: **{len(self.sources)}** | Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
            "| ID | Título | Autoridad | Tipo | Canal | En Cuaderno | URL |",
            "| :---: | :--- | :---: | :---: | :---: | :---: | :--- |"
        ]

        for s in self.sources:
            en_cuaderno_badge = "✅ Sí" if s.get("en_cuaderno") else "⏳ Pendiente"
            stars = "⭐" * s.get("autoridad", 3)
            lines.append(
                f"| `{s['id']}` | **{s['titulo']}** | {stars} ({s['autoridad']}) | `{s['tipo']}` | `{s['canal']}` | {en_cuaderno_badge} | [{s['url_canonica']}]({s['url']}) |"
            )

        with open(self.indice_md, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        print(f"[OK] Índice generado en: {self.indice_md}")

def main():
    if len(sys.argv) < 3:
        print("Uso: sources_manager.py <workspace_dir> <comando> [argumentos...]")
        print("Comandos disponibles:")
        print("  add <url> <titulo> <tipo> <canal> <autoridad>")
        print("  index")
        sys.exit(1)

    workspace_dir = sys.argv[1]
    comando = sys.argv[2]
    mgr = SourcesManager(workspace_dir)

    if comando == "add":
        url = sys.argv[3] if len(sys.argv) > 3 else ""
        titulo = sys.argv[4] if len(sys.argv) > 4 else "Fuente"
        tipo = sys.argv[5] if len(sys.argv) > 5 else "web"
        canal = sys.argv[6] if len(sys.argv) > 6 else "grounding"
        autoridad = int(sys.argv[7]) if len(sys.argv) > 7 else 3
        mgr.add_source(url, titulo, tipo, canal, autoridad)
        mgr.generate_index_markdown()
    elif comando == "index":
        mgr.generate_index_markdown()
    else:
        print(f"Comando desconocido: {comando}")
        sys.exit(1)

if __name__ == "__main__":
    main()
