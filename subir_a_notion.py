#!/usr/bin/env python3
"""Sube los archivos del viaje China 2027 a Notion via API."""

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("Error: variable de entorno NOTION_TOKEN no definida.")
    print("Configúrala con: export NOTION_TOKEN=secret_...")
    sys.exit(1)

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


# ---------------------------------------------------------------------------
# API helper
# ---------------------------------------------------------------------------

def notion_request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=_HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"\nError HTTP {e.code} en {method} {path}:")
        try:
            print(json.dumps(json.loads(error_body), indent=2, ensure_ascii=False))
        except Exception:
            print(error_body)
        raise
    finally:
        time.sleep(0.35)


# ---------------------------------------------------------------------------
# Property builders
# ---------------------------------------------------------------------------

def rich_text(content):
    content = (content or "").strip()
    if not content:
        return []
    if len(content) > 2000:
        content = content[:1997] + "..."
    return [{"type": "text", "text": {"content": content}}]


def text_prop(value):
    return {"rich_text": rich_text(value)}


def title_prop(value):
    return {"title": rich_text(value or "Sin título")}


def select_prop(value):
    value = (value or "").strip()
    if not value or value == "—":
        return {"select": None}
    if len(value) > 100:
        value = value[:97] + "..."
    return {"select": {"name": value}}


def date_prop(value):
    value = (value or "").strip()
    if not value or value == "—":
        return {"date": None}
    return {"date": {"start": value}}


def number_prop(value):
    value = (value or "").strip()
    if not value:
        return {"number": None}
    try:
        return {"number": int(value)}
    except ValueError:
        pass
    try:
        return {"number": float(value)}
    except ValueError:
        return {"number": None}


# ---------------------------------------------------------------------------
# Core creators
# ---------------------------------------------------------------------------

def create_parent_page():
    print("📁 Creando página principal 'Viaje China 2027'...")
    page = notion_request("POST", "/pages", {
        "parent": {"type": "workspace", "workspace": True},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": "Viaje China 2027"}}]},
        },
        "children": [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {
                        "content": "Viaje a China — Mayo/Junio 2027. "
                                   "Itinerario de 19 días: Beijing · Xi'an · Chengdu · Shanghai."
                    }}],
                    "icon": {"type": "emoji", "emoji": "🇨🇳"},
                    "color": "red_background",
                },
            }
        ],
    })
    url = f"https://notion.so/{page['id'].replace('-', '')}"
    print(f"  ✅ Página principal: {url}")
    return page["id"]


def create_database(parent_page_id, title, properties):
    return notion_request("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    })


def add_row(db_id, properties):
    return notion_request("POST", "/pages", {
        "parent": {"database_id": db_id},
        "properties": properties,
    })


# ---------------------------------------------------------------------------
# CSV uploaders
# ---------------------------------------------------------------------------

def upload_itinerario(parent_id):
    print("\n📅 Subiendo itinerario.csv...")
    db = create_database(parent_id, "Itinerario China 2027", {
        "Actividad": {"title": {}},
        "Fecha": {"date": {}},
        "Dia": {"number": {}},
        "Ciudad": {"select": {}},
        "Bloque": {"select": {}},
        "Tipo": {"select": {}},
        "Lugar": {"rich_text": {}},
        "Transporte": {"rich_text": {}},
        "Reserva": {"rich_text": {}},
        "Notas": {"rich_text": {}},
    })
    db_id = db["id"]

    with open(os.path.join(SCRIPT_DIR, "itinerario.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows):
        props = {
            "Actividad": title_prop(row.get("Actividad")),
            "Dia": number_prop(row.get("Dia")),
            "Ciudad": select_prop(row.get("Ciudad")),
            "Bloque": select_prop(row.get("Bloque")),
            "Tipo": select_prop(row.get("Tipo")),
            "Lugar": text_prop(row.get("Lugar")),
            "Transporte": text_prop(row.get("Transporte")),
            "Reserva": text_prop(row.get("Reserva")),
            "Notas": text_prop(row.get("Notas")),
        }
        fecha = date_prop(row.get("Fecha"))
        if fecha["date"] is not None:
            props["Fecha"] = fecha

        add_row(db_id, props)
        print(f"  [{i+1}/{len(rows)}] {row.get('Actividad', '')[:60]}")

    url = f"https://notion.so/{db_id.replace('-', '')}"
    print(f"  ✅ Itinerario: {url}")
    return db_id


def upload_hoteles(parent_id):
    print("\n🏨 Subiendo hoteles.csv...")
    db = create_database(parent_id, "Hoteles China 2027", {
        "Hotel": {"title": {}},
        "Ciudad": {"select": {}},
        "Tipo": {"rich_text": {}},
        "Cocina": {"rich_text": {}},
        "Gym": {"rich_text": {}},
        "Metro_cercano": {"rich_text": {}},
        "Noches": {"number": {}},
        "Por_que": {"rich_text": {}},
    })
    db_id = db["id"]

    with open(os.path.join(SCRIPT_DIR, "hoteles.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows):
        props = {
            "Hotel": title_prop(row.get("Hotel")),
            "Ciudad": select_prop(row.get("Ciudad")),
            "Tipo": text_prop(row.get("Tipo")),
            "Cocina": text_prop(row.get("Cocina")),
            "Gym": text_prop(row.get("Gym")),
            "Metro_cercano": text_prop(row.get("Metro_cercano")),
            "Noches": number_prop(row.get("Noches")),
            "Por_que": text_prop(row.get("Por_que")),
        }
        add_row(db_id, props)
        print(f"  [{i+1}/{len(rows)}] {row.get('Hotel', '')[:60]}")

    url = f"https://notion.so/{db_id.replace('-', '')}"
    print(f"  ✅ Hoteles: {url}")
    return db_id


def upload_restaurantes(parent_id):
    print("\n🍜 Subiendo restaurantes.csv...")
    db = create_database(parent_id, "Restaurantes China 2027", {
        "Restaurante": {"title": {}},
        "Ciudad": {"select": {}},
        "Cocina": {"rich_text": {}},
        "Michelin": {"rich_text": {}},
        "Reserva": {"rich_text": {}},
        "Anticipacion_reserva": {"rich_text": {}},
        "Picante": {"rich_text": {}},
        "Apto_sin_pescado": {"rich_text": {}},
        "Metro": {"rich_text": {}},
        "Notas": {"rich_text": {}},
    })
    db_id = db["id"]

    with open(os.path.join(SCRIPT_DIR, "restaurantes.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows):
        props = {
            "Restaurante": title_prop(row.get("Restaurante")),
            "Ciudad": select_prop(row.get("Ciudad")),
            "Cocina": text_prop(row.get("Cocina")),
            "Michelin": text_prop(row.get("Michelin")),
            "Reserva": text_prop(row.get("Reserva")),
            "Anticipacion_reserva": text_prop(row.get("Anticipacion_reserva")),
            "Picante": text_prop(row.get("Picante")),
            "Apto_sin_pescado": text_prop(row.get("Apto_sin_pescado")),
            "Metro": text_prop(row.get("Metro")),
            "Notas": text_prop(row.get("Notas")),
        }
        add_row(db_id, props)
        print(f"  [{i+1}/{len(rows)}] {row.get('Restaurante', '')[:60]}")

    url = f"https://notion.so/{db_id.replace('-', '')}"
    print(f"  ✅ Restaurantes: {url}")
    return db_id


# ---------------------------------------------------------------------------
# Markdown → Notion blocks
# ---------------------------------------------------------------------------

_SEPARATOR_RE = re.compile(r"^\|[-:| ]+\|$")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")


def _parse_table(table_lines):
    data_lines = [l for l in table_lines if not _SEPARATOR_RE.match(l.strip())]
    if not data_lines:
        return None

    def parse_row(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]

    rows = [parse_row(l) for l in data_lines]
    table_width = max(len(r) for r in rows)

    row_blocks = []
    for r in rows:
        cells = (r + [""] * table_width)[:table_width]
        row_blocks.append({
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [[{"type": "text", "text": {"content": c[:2000]}}] for c in cells],
            },
        })

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": True,
            "has_row_header": False,
        },
        "children": row_blocks,
    }


def parse_markdown_blocks(md_text):
    blocks = []
    lines = md_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.startswith("```"):
            lang = line[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code = "\n".join(code_lines)[:2000]
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": code}}],
                    "language": lang if lang in {
                        "bash", "python", "json", "javascript", "typescript",
                        "css", "html", "sql", "shell", "yaml", "markdown",
                        "java", "go", "rust", "ruby", "php", "swift",
                        "kotlin", "c", "cpp", "csharp",
                    } else "plain text",
                },
            })
            i += 1
            continue

        # Table block
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            block = _parse_table(table_lines)
            if block:
                blocks.append(block)
            continue

        # Headings
        if line.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": rich_text(line[4:])},
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": rich_text(line[3:])},
            })
        elif line.startswith("# "):
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": rich_text(line[2:])},
            })
        # Checkboxes
        elif line.startswith("- [ ] "):
            blocks.append({
                "object": "block", "type": "to_do",
                "to_do": {"rich_text": rich_text(line[6:]), "checked": False},
            })
        elif re.match(r"^- \[x\] ", line, re.IGNORECASE):
            blocks.append({
                "object": "block", "type": "to_do",
                "to_do": {"rich_text": rich_text(line[6:]), "checked": True},
            })
        # Bullet list
        elif line.startswith("- "):
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": rich_text(line[2:])},
            })
        # Numbered list
        elif _NUMBERED_RE.match(line):
            content = _NUMBERED_RE.sub("", line)
            blocks.append({
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": rich_text(content)},
            })
        # Blockquote
        elif line.startswith("> "):
            blocks.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": rich_text(line[2:])},
            })
        # Divider
        elif line.strip() in ("---", "***", "___"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        # Empty line
        elif not line.strip():
            pass
        # Paragraph
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": rich_text(line)},
            })

        i += 1

    return blocks


def append_blocks(page_id, blocks):
    """Send blocks to a page. Tables are sent individually; others in batches of 100."""
    total = len(blocks)
    sent = 0
    batch = []

    def flush_batch():
        nonlocal sent
        if not batch:
            return
        notion_request("PATCH", f"/blocks/{page_id}/children", {"children": batch})
        sent += len(batch)
        print(f"  Bloques {sent-len(batch)+1}-{sent}/{total} subidos")
        batch.clear()

    for block in blocks:
        if block["type"] == "table":
            flush_batch()
            notion_request("PATCH", f"/blocks/{page_id}/children", {"children": [block]})
            sent += 1
            n_rows = len(block.get("children", []))
            print(f"  Tabla ({n_rows} filas) subida. Total: {sent}/{total}")
        else:
            batch.append(block)
            if len(batch) >= 100:
                flush_batch()

    flush_batch()


def upload_guia(parent_id):
    print("\n📖 Subiendo guia.md...")
    page = notion_request("POST", "/pages", {
        "parent": {"type": "page_id", "page_id": parent_id},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": "Guía China 2027"}}]},
        },
    })
    page_id = page["id"]

    with open(os.path.join(SCRIPT_DIR, "guia.md"), encoding="utf-8") as f:
        content = f.read()

    blocks = parse_markdown_blocks(content)
    print(f"  Convirtiendo {len(blocks)} bloques de markdown...")
    append_blocks(page_id, blocks)

    url = f"https://notion.so/{page_id.replace('-', '')}"
    print(f"  ✅ Guía: {url}")
    return page_id


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("🇨🇳 Subiendo archivos a Notion — Viaje China 2027")
    print("=" * 55)

    parent_id = create_parent_page()
    upload_itinerario(parent_id)
    upload_hoteles(parent_id)
    upload_restaurantes(parent_id)
    upload_guia(parent_id)

    print("\n" + "=" * 55)
    print("✅ ¡Todo listo en Notion!")
    url = f"https://notion.so/{parent_id.replace('-', '')}"
    print(f"🔗 Página principal: {url}")


if __name__ == "__main__":
    main()
