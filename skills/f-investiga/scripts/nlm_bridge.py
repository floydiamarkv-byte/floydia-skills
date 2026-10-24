#!/usr/bin/env python3
"""
nlm_bridge.py - Puente determinista entre Searcher Floydia y Google NotebookLM CLI (nlm).
Permite crear cuadernos, subir fuentes individuales o por lotes, y consultar el cuaderno.
"""

import sys
import os
import json
import subprocess
import shutil

NLM_BIN = shutil.which("nlm") or os.path.expanduser("~/.local/bin/nlm")

def run_nlm_cmd(args: list) -> dict:
    """Ejecuta un comando nlm y devuelve la salida parseada o texto."""
    if not os.path.exists(NLM_BIN) and not shutil.which("nlm"):
        return {"success": False, "error": f"nlm CLI no encontrado en {NLM_BIN}"}

    cmd = [NLM_BIN] + args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = res.stdout.strip()
        stderr = res.stderr.strip()
        
        # Intentar parsear JSON si está disponible
        try:
            data = json.loads(output)
            return {"success": res.returncode == 0, "data": data, "raw": output}
        except Exception:
            return {"success": res.returncode == 0, "raw": output, "stderr": stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout al ejecutar comando nlm"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_notebook(title: str) -> dict:
    """Crea un nuevo cuaderno en NotebookLM."""
    res = run_nlm_cmd(["create", "notebook", title])
    if res.get("success") and "data" in res:
        return res["data"]
    # Fallback si devuelve texto formateado
    raw = res.get("raw", "")
    return {"raw": raw, "success": res.get("success", False)}

def add_source_url(notebook_id: str, url: str, title: str = None) -> dict:
    """Añade una URL pública como fuente."""
    args = ["source", "add", notebook_id, "--url", url, "--wait"]
    if title:
        args.extend(["--title", title])
    return run_nlm_cmd(args)

def add_source_file(notebook_id: str, file_path: str, title: str = None) -> dict:
    """Añade un archivo local o documento de texto como fuente."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"Archivo no existe: {file_path}"}
    args = ["source", "add", notebook_id, "--file", file_path, "--wait"]
    if title:
        args.extend(["--title", title])
    return run_nlm_cmd(args)

def query_notebook(notebook_id: str, prompt: str) -> dict:
    """Ejecuta una consulta analítica contra el cuaderno."""
    args = ["query", "notebook", notebook_id, prompt]
    return run_nlm_cmd(args)

def main():
    if len(sys.argv) < 2:
        print("Uso: nlm_bridge.py <comando> [args...]")
        print("Comandos: create <titulo> | add-url <nb_id> <url> [titulo] | add-file <nb_id> <path> [titulo] | query <nb_id> <prompt>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "create":
        title = sys.argv[2] if len(sys.argv) > 2 else "INVESTIGACION_SEARCHER_FLOYDIA"
        result = create_notebook(title)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "add-url":
        nb_id = sys.argv[2]
        url = sys.argv[3]
        title = sys.argv[4] if len(sys.argv) > 4 else None
        res = add_source_url(nb_id, url, title)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "add-file":
        nb_id = sys.argv[2]
        fpath = sys.argv[3]
        title = sys.argv[4] if len(sys.argv) > 4 else None
        res = add_source_file(nb_id, fpath, title)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "query":
        nb_id = sys.argv[2]
        prompt = sys.argv[3]
        res = query_notebook(nb_id, prompt)
        print(res.get("raw", res.get("error", "")))
    else:
        print(f"Comando no reconocido: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
