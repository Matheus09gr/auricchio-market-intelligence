#!/usr/bin/env python3
from pathlib import Path
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
METALS_JSON = ROOT / "metals.json"

ALLOWED_METALS = {
    "tin": {"name": "Estanho", "symbol": "Sn"},
    "copper": {"name": "Cobre", "symbol": "Cu"},
    "zinc": {"name": "Zinco", "symbol": "Zn"},
    "nickel": {"name": "Níquel", "symbol": "Ni"},
    "tungsten": {"name": "Tungstênio", "symbol": "W"},
}

META_RE = re.compile(
    r'<script[^>]*id=["\']report-meta["\'][^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

REQUIRED_FIELDS = ["metal", "date", "title", "bias", "physical", "note"]

def fail(message):
    print(f"ERRO: {message}", file=sys.stderr)
    raise SystemExit(1)

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Não foi possível ler {path.relative_to(ROOT)}: {exc}")

def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

def parse_metadata(html_path):
    html = html_path.read_text(encoding="utf-8")
    match = META_RE.search(html)
    if not match:
        fail(
            f"{html_path.name}: bloco <script id='report-meta' type='application/json'> não encontrado."
        )
    try:
        meta = json.loads(match.group(1).strip())
    except json.JSONDecodeError as exc:
        fail(f"{html_path.name}: JSON de metadados inválido: {exc}")

    missing = [k for k in REQUIRED_FIELDS if not str(meta.get(k, "")).strip()]
    if missing:
        fail(f"{html_path.name}: campos obrigatórios ausentes: {', '.join(missing)}")

    metal = str(meta["metal"]).strip().lower()
    if metal not in ALLOWED_METALS:
        fail(f"{html_path.name}: metal '{metal}' não é aceito.")

    date = str(meta["date"]).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        fail(f"{html_path.name}: data '{date}' deve estar em AAAA-MM-DD.")

    meta["metal"] = metal
    return meta

def display_date(date):
    y, m, d = date.split("-")
    return f"{d}/{m}/{y}"

def update_reports(meta, snapshot_rel):
    metal = meta["metal"]
    reports_path = ROOT / metal / "reports.json"

    if reports_path.exists():
        data = load_json(reports_path)
    else:
        data = {
            "metal": ALLOWED_METALS[metal]["name"],
            "symbol": ALLOWED_METALS[metal]["symbol"],
            "updated_at": None,
            "reports": [],
        }

    entry = {
        "date": meta["date"],
        "display_date": display_date(meta["date"]),
        "title": meta["title"],
        "file": f"./reports/{snapshot_rel.name}",
        "bias": meta["bias"],
        "physical": meta["physical"],
        "note": meta["note"],
    }

    reports = [r for r in data.get("reports", []) if r.get("date") != meta["date"]]
    reports.append(entry)
    reports.sort(key=lambda r: r.get("date", ""), reverse=True)

    data["reports"] = reports
    data["updated_at"] = reports[0]["date"] if reports else meta["date"]
    save_json(reports_path, data)

def update_metals(all_meta):
    data = load_json(METALS_JSON)
    metal_map = {m["id"]: m for m in data.get("metals", [])}

    for meta in all_meta:
        metal = meta["metal"]
        if metal not in metal_map:
            fail(f"Metal '{metal}' não encontrado em metals.json.")

        item = metal_map[metal]
        item["status"] = "available"
        item["last_report"] = display_date(meta["date"])
        item["bias"] = meta["bias"]
        item["physical"] = meta["physical"]
        item["note"] = meta["note"]

    dates = [m["date"] for m in all_meta]
    if dates:
        current = data.get("updated_at")
        newest = max(dates + ([current] if current else []))
        data["updated_at"] = newest

    save_json(METALS_JSON, data)

def main():
    html_files = sorted(INCOMING.glob("*.html"))

    if not html_files:
        print("Nenhum HTML em incoming/. Nada a processar.")
        return

    parsed = []
    seen = set()

    # Validar tudo antes de alterar o repositório.
    for html_path in html_files:
        meta = parse_metadata(html_path)
        key = (meta["metal"], meta["date"])
        if key in seen:
            fail(f"Mais de um arquivo para {meta['metal']} em {meta['date']}.")
        seen.add(key)
        parsed.append((html_path, meta))

    # Processar.
    processed_meta = []
    for html_path, meta in parsed:
        metal = meta["metal"]
        metal_dir = ROOT / metal
        reports_dir = metal_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        snapshot = reports_dir / f"{meta['date']}.html"
        current = metal_dir / "index.html"

        shutil.copy2(html_path, snapshot)
        shutil.copy2(html_path, current)

        update_reports(meta, snapshot)
        processed_meta.append(meta)

        # Remove o arquivo de entrada depois de processado.
        html_path.unlink()

        print(
            f"OK: {metal} {meta['date']} -> "
            f"{snapshot.relative_to(ROOT)} + {current.relative_to(ROOT)}"
        )

    update_metals(processed_meta)
    print(f"Processados: {len(processed_meta)} arquivo(s).")

if __name__ == "__main__":
    main()
