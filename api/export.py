"""Portable, escaped audit evidence exports; never a compliance certificate."""
from html import escape
from datetime import datetime
import math
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from worker.engine.categories import CATEGORY_LABELS, enrich_issue

IMPACTS = {
    "visual_contrast": ("Low vision and color perception: review contrast, legibility and visual alternatives.", "Vedere slabă și percepția culorilor: verifică contrastul, lizibilitatea și alternativele vizuale."),
    "screen_reader": ("Blind users need meaningful names, labels and compatible semantics.", "Utilizatorii nevăzători au nevoie de nume, etichete și semantică accesibile."),
    "motor_keyboard": ("Keyboard and motor access require reachable controls and a way to leave every component.", "Accesul prin tastatură necesită controale accesibile și posibilitatea de a părăsi fiecare componentă."),
    "structure_navigation": ("Headings, landmarks and document language support orientation and comprehension.", "Titlurile, reperele și limba documentului ajută orientarea și înțelegerea."),
}


def text(value):
    return escape(str(value if value is not None else "Not recorded"), quote=True)


def safe_url(value):
    value = str(value or "")
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ("https", "http") and parsed.netloc else ""
    except ValueError:
        return ""


def timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        return "—"
    tenths = round(value * 10)
    minutes, seconds = divmod(tenths, 600)
    return f"{minutes:02d}:{seconds / 10:04.1f}"


def generate_html_report(report_data, *, timeline=None, nodes=None, metadata=None):
    """Render standalone printable HTML without mutating the canonical report."""
    report = report_data
    lang = "en" if report.get("lang") == "en" else "ro"
    ro = lang == "ro"
    def tr(en, romanian):
        return romanian if ro else en
    metadata = metadata or {}
    completed = metadata.get("completed_at")
    local_completed = None
    try:
        parsed = datetime.fromisoformat(completed.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            local_completed = parsed.astimezone(ZoneInfo("Europe/Bucharest")).isoformat()
    except (AttributeError, TypeError, ValueError):
        pass
    groups = {key: [] for key in CATEGORY_LABELS}
    for issue in report.get("issues", []):
        item = enrich_issue(issue)
        groups[item["category"]].append(item)
    score = report.get("score")
    valid_score = isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(score)
    score_class = "good" if valid_score and score >= 90 else "attention" if valid_score and score >= 50 else "critical"
    url = safe_url(report.get("url"))
    target = f'<a href="{text(url)}">{text(report.get("url"))}</a>' if url else text(report.get("url"))
    sections = []
    for category, issues in groups.items():
        critical = any(i.get("severity") in ("critical", "serious") for i in issues)
        status = tr("Critical barriers", "Bariere critice") if critical else tr("Needs attention", "Necesită atenție") if issues else tr("No automated findings", "Fără constatări automate")
        cards = []
        for issue in issues:
            reference = safe_url(issue.get("help_url"))
            citation = f'<a href="{text(reference)}">{text(tr("Rule reference", "Referință regulă"))}</a>' if reference else text(tr("Reference not recorded", "Referință neînregistrată"))
            cards.append(f'''<article><h3>{text(issue.get("title") or issue.get("rule"))}</h3>
<p><strong>{text(issue.get("severity"))}</strong> · {text(issue.get("rule"))} · {timestamp(issue.get("timestamp"))}</p>
<p><code>{text(issue.get("selector"))}</code></p><p>{text(issue.get("recommendation"))}</p><p>{citation}</p></article>''')
        sections.append(f'<section><h2>{text(CATEGORY_LABELS[category][lang])}</h2><p>{text(IMPACTS[category][int(ro)])}</p><p><strong>{text(status)}</strong> ({len(issues)})</p>{"".join(cards)}</section>')
    node_map = {node.get("id"): node for node in (nodes or {}).get("nodes", [])}
    rows = []
    for entry in (timeline or {}).get("entries", []):
        bbox = node_map.get(entry.get("node_id"), {}).get("bbox")
        rows.append(f'<tr><td>{timestamp(entry.get("start"))}–{timestamp(entry.get("end"))}</td><td>{text(entry.get("text"))}</td><td>{text(bbox)}</td></tr>')
    empty = tr("Transcript was not recorded.", "Transcriptul nu a fost înregistrat.")
    transcript = f'<table><thead><tr><th>{tr("Time", "Timp")}</th><th>{tr("Announcement", "Anunț")}</th><th>Bounding box</th></tr></thead><tbody>{"".join(rows)}</tbody></table>' if rows else f'<p>{empty}</p>'
    notice = tr("Automated page assessment, not a certification or a WCAG 2.1 AA conformance verdict. The score is a ClearPath heuristic, not a percentage of legal compliance. Manual keyboard, assistive technology and user testing remain necessary. The video is a narrated simulation, not a recording of a real screen reader.", "Evaluare automată a paginii, nu certificare sau verdict de conformitate WCAG 2.1 AA. Scorul este o euristică ClearPath, nu procent de conformitate legală. Sunt necesare verificări manuale cu tastatura, tehnologii asistive și utilizatori. Videoul este o simulare narată, nu înregistrarea unui cititor de ecran real.")
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ClearPath — {text(report.get("title") or report.get("url"))}</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;color:#17212b;max-width:1000px;margin:40px auto;padding:0 24px}}h1,h2,h3{{line-height:1.25}}h2{{border-bottom:2px solid #ccd5df;padding-bottom:10px}}article{{border:1px solid #ccd5df;border-radius:8px;padding:16px;margin:16px 0;break-inside:avoid}}a{{color:#174f94;overflow-wrap:anywhere}}code{{white-space:pre-wrap;overflow-wrap:anywhere}}.score{{display:inline-block;padding:12px 24px;border:3px solid;border-radius:12px;font-size:28px;font-weight:bold}}.good{{color:#176038}}.attention{{color:#805200}}.critical{{color:#a12525}}aside{{padding:16px;background:#f0f3f6;border-left:4px solid #536b85}}table{{width:100%;border-collapse:collapse}}td,th{{border:1px solid #ccd5df;padding:8px;text-align:left;overflow-wrap:anywhere}}@page{{size:A4;margin:18mm}}@media print{{body{{margin:0;padding:0;max-width:none;font-size:10pt}}h2,h3{{break-after:avoid}}thead{{display:table-header-group}}tr{{break-inside:avoid}}a{{color:inherit}}}}</style></head><body>
<header><p>ClearPath · {text(tr("Accessibility review", "Evaluare accesibilitate"))}</p><h1>{text(report.get("title") or report.get("url"))}</h1><p>{target}</p><p>ID: {text(report.get("id"))}</p><p>{text(tr("Analysis completed (ISO 8601)", "Analiză finalizată (ISO 8601)"))}: {text(completed)}</p><p>Europe/Bucharest: {text(local_completed)}</p><p>{text(tr("Recorded engine versions", "Versiuni motor înregistrate"))}: {text(metadata.get("engine_versions"))}</p><p class="score {score_class}">{text(score if valid_score else "—")} / 100</p><p>{len(report.get("issues", []))} {tr("findings", "constatări")} · {tr("Keyboard trap", "Blocare tastatură")}: {text(bool(report.get("focus_trap")))}</p></header>
<aside>{notice}</aside>{"".join(sections)}<section><h2>{tr("Narrated traversal transcript", "Transcriptul parcurgerii narate")}</h2>{transcript}</section></body></html>'''
