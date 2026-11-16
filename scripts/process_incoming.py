#!/usr/bin/env python3
from pathlib import Path
import html as html_lib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
METALS_JSON = ROOT / "metals.json"

ALLOWED_METALS = {
    "tin": {"name": "Estanho", "symbol": "Sn", "aliases": ["tin", "estanho"]},
    "copper": {"name": "Cobre", "symbol": "Cu", "aliases": ["copper", "cobre"]},
    "zinc": {"name": "Zinco", "symbol": "Zn", "aliases": ["zinc", "zinco"]},
    "nickel": {"name": "Níquel", "symbol": "Ni", "aliases": ["nickel", "níquel", "niquel"]},
    "tungsten": {"name": "Tungstênio", "symbol": "W", "aliases": ["tungsten", "tungstênio", "tungstenio"]},
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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def strip_tags(text):
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_date_br(value):
    d, m, y = value.split("/")
    return f"{y}-{m}-{d}"


def contains_word(text, word):
    return re.search(rf"(?<![\wÀ-ÿ]){re.escape(word)}(?![\wÀ-ÿ])", text, flags=re.I) is not None


def infer_metal(html_path, html):
    # Prioriza o nome do arquivo e o <title>, evitando falsos positivos como 'tin' em 'testing'.
    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    title = strip_tags(title_match.group(1)) if title_match else ""
    sources = [html_path.stem, title]
    for source in sources:
        for metal, cfg in ALLOWED_METALS.items():
            if any(contains_word(source, alias) for alias in cfg["aliases"]):
                return metal
    # Fallback: busca apenas no começo visível do documento, com palavra inteira.
    visible = strip_tags(html[:25000])
    for metal, cfg in ALLOWED_METALS.items():
        if any(contains_word(visible, alias) for alias in cfg["aliases"]):
            return metal
    return None


def infer_date(html):
    # Ordem desenhada para os observatórios Auricchio atuais.
    direct_patterns = [
        r"RELAT[ÓO]RIO-BASE\s*[·:\-]\s*(\d{2}/\d{2}/\d{4})",
        r"Research de refer[eê]ncia:\s*(\d{2}/\d{2}/\d{4})",
        r"PDF(?:\s*:\s*cabe[cç]alho|\s+datado\s+de)\s*(\d{2}/\d{2}/\d{4})",
        r"Relat[óo]rio-base:.*?(\d{2}/\d{2}/\d{4})",
        r"Fonte principal:.*?(\d{2}/\d{2}/\d{4})",
        r"Research publicado:\s*(\d{2}/\d{2}/\d{4})",
    ]
    for pattern in direct_patterns:
        m = re.search(pattern, html, flags=re.I | re.S)
        if m:
            return normalize_date_br(m.group(1))

    # Formato 'FASTMARKETS · 13 NOV 2026'.
    m = re.search(r"FASTMARKETS\s*[·:\-]\s*(\d{1,2})\s+([A-Z]{3})\s+(\d{4})", html, flags=re.I)
    if m:
        months = {"JAN":"01","FEV":"02","FEB":"02","MAR":"03","ABR":"04","APR":"04","MAI":"05","MAY":"05","JUN":"06","JUL":"07","AGO":"08","AUG":"08","SET":"09","SEP":"09","OUT":"10","OCT":"10","NOV":"11","DEZ":"12","DEC":"12"}
        day, mon, year = m.groups()
        mon = months.get(mon.upper())
        if mon:
            return f"{year}-{mon}-{int(day):02d}"

    # Último recurso: primeira data visível.
    m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", strip_tags(html))
    return normalize_date_br(m.group(1)) if m else None


def infer_title(html, metal):
    patterns = [
        r"<b>Research-base:</b>\s*[“\"]([^”\"]+)[”\"]",
        r"<b>Relat[óo]rio-base:</b>.*?[“\"]([^”\"]+)[”\"]",
        r"<i>\s*Research\s*[–-]\s*([^<]+)</i>",
        r"Relat[óo]rio-base:.*?[“\"]([^”\"]+)[”\"]",
        r"Fonte principal:.*?[“\"]([^”\"]+)[”\"]",
    ]
    for pattern in patterns:
        m = re.search(pattern, html, flags=re.I | re.S)
        if m:
            return strip_tags(m.group(1))
    m = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if m:
        return re.sub(r"^Auricchio\s*\|\s*", "", strip_tags(m.group(1)), flags=re.I)
    return f"Observatório do {ALLOWED_METALS[metal]['name']}"


def infer_bias(html, metal):
    patterns = [
        r"curto\s*:\s*\[\s*\[\s*['\"]Vi[eé]s(?:\s+do\s+quadro)?['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        r"curto\s*:\s*\[\s*\[\s*['\"]Leitura['\"]\s*,\s*['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        m = re.search(pattern, html, flags=re.I | re.S)
        if m:
            return strip_tags(m.group(1))
    defaults = {
        "copper": "Bearish / vulnerável",
        "zinc": "Neutro",
        "nickel": "Em teste",
        "tin": "Bearish",
        "tungsten": "Neutro",
    }
    return defaults[metal]


def infer_physical(html, metal):
    text = strip_tags(html).lower()
    if "físico heterogêneo" in text or "fisico heterogeneo" in text:
        return "Misto"
    if "físico segue apertado" in text or "fisico segue apertado" in text or "físico apertado" in text or "fisico apertado" in text:
        return "Apertado"
    if "mercado físico: aperto" in text or "mercado fisico: aperto" in text:
        return "Apertado"
    if "muito metal visível" in text or "muito metal visivel" in text or "estoques visíveis elevados" in text or "estoques visiveis elevados" in text:
        return "Folgado"
    if "não descreve aperto físico generalizado" in text or "nao descreve aperto fisico generalizado" in text:
        return "Folgado"
    return {"copper":"Misto","zinc":"Apertado","nickel":"Folgado","tin":"Apertado","tungsten":"Misto"}[metal]


def infer_note(html, metal):
    m = re.search(r'<div[^>]*class=["\'][^"\']*\bfinal\b[^"\']*["\'][^>]*>.*?<p>(.*?)</p>', html, flags=re.I | re.S)
    if not m:
        m = re.search(r'<div[^>]*class=["\'][^"\']*\blede\b[^"\']*["\'][^>]*>(.*?)</div>', html, flags=re.I | re.S)
    note = strip_tags(m.group(1)) if m else f"Análise atualizada do mercado de {ALLOWED_METALS[metal]['name']}."
    return note if len(note) <= 240 else note[:237].rstrip() + "..."


def inject_metadata(html, meta):
    block = '\n<script id="report-meta" type="application/json">\n' + json.dumps(meta, ensure_ascii=False, indent=2) + '\n</script>\n'
    if META_RE.search(html):
        return META_RE.sub(block.strip(), html, count=1)
    pos = html.lower().rfind("</body>")
    return html[:pos] + block + html[pos:] if pos >= 0 else html + block


def validate_meta(meta, html_path):
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


def parse_metadata(html_path):
    html = html_path.read_text(encoding="utf-8")
    match = META_RE.search(html)
    if match:
        try:
            meta = json.loads(match.group(1).strip())
        except json.JSONDecodeError as exc:
            fail(f"{html_path.name}: JSON de metadados inválido: {exc}")
        return validate_meta(meta, html_path), html

    metal = infer_metal(html_path, html)
    if not metal:
        fail(f"{html_path.name}: não foi possível identificar o metal automaticamente.")
    date = infer_date(html)
    if not date:
        fail(f"{html_path.name}: não foi possível identificar a data automaticamente.")
    meta = validate_meta({
        "metal": metal,
        "date": date,
        "title": infer_title(html, metal),
        "bias": infer_bias(html, metal),
        "physical": infer_physical(html, metal),
        "note": infer_note(html, metal),
    }, html_path)
    print(f"LEGADO: {html_path.name} -> {meta['metal']} {meta['date']} | {meta['bias']} | físico: {meta['physical']}")
    return meta, inject_metadata(html, meta)


def display_date(date):
    y, m, d = date.split("-")
    return f"{d}/{m}/{y}"


def update_reports(meta, snapshot_rel):
    metal = meta["metal"]
    reports_path = ROOT / metal / "reports.json"
    if reports_path.exists():
        data = load_json(reports_path)
    else:
        data = {"metal": ALLOWED_METALS[metal]["name"], "symbol": ALLOWED_METALS[metal]["symbol"], "updated_at": None, "reports": []}
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
        data["updated_at"] = max(dates + ([current] if current else []))
    save_json(METALS_JSON, data)


def main():
    html_files = sorted(INCOMING.glob("*.html"))
    if not html_files:
        print("Nenhum HTML em incoming/. Nada a processar.")
        return

    parsed = []
    seen = set()
    for html_path in html_files:
        meta, normalized_html = parse_metadata(html_path)
        key = (meta["metal"], meta["date"])
        if key in seen:
            fail(f"Mais de um arquivo para {meta['metal']} em {meta['date']}.")
        seen.add(key)
        parsed.append((html_path, meta, normalized_html))

    processed_meta = []
    for html_path, meta, normalized_html in parsed:
        metal_dir = ROOT / meta["metal"]
        reports_dir = metal_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        snapshot = reports_dir / f"{meta['date']}.html"
        current = metal_dir / "index.html"
        snapshot.write_text(normalized_html, encoding="utf-8")
        current.write_text(normalized_html, encoding="utf-8")
        update_reports(meta, snapshot)
        processed_meta.append(meta)
        html_path.unlink()
        print(f"OK: {meta['metal']} {meta['date']} -> {snapshot.relative_to(ROOT)} + {current.relative_to(ROOT)}")

    update_metals(processed_meta)
    print(f"Processados: {len(processed_meta)} arquivo(s).")


if __name__ == "__main__":
    main()
