"""Track M2: Announcement engine converting nodes into spoken Romanian screen-reader announcements."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import MAX_EVENTS, SAMPLES, read_json, write_json


def _speech(node: dict) -> str:
    """Build a Romanian name, role, state announcement without empty segments."""
    role = node.get("role")
    name = (node.get("name") or "").strip()
    states = node.get("states") or {}
    value = node.get("value")
    parts = [name] if name else []
    if role == "heading":
        parts.append("titlu" + (f" nivel {node['level']}" if node.get("level") else ""))
    elif role in ("link", "button"):
        parts.append({"link": "link", "button": "buton"}[role])
    elif role in ("textbox", "input"):
        parts.append("casetă de editare")
        if value is None or not str(value).strip():
            parts.append("necompletat")
        else:
            parts.append(f"conține {value}")
    elif role in ("checkbox", "radio"):
        parts.append("casetă de bifare" if role == "checkbox" else "buton radio")
        checked = states.get("checked")
        if checked == "mixed":
            parts.append("parțial bifat")
        elif checked is not None:
            parts.append(("bifat" if checked else "nebifat") if role == "checkbox"
                         else ("selectat" if checked else "neselectat"))
    elif role == "combobox":
        parts.append("casetă combinată")
        if value is not None and str(value).strip():
            parts.append(str(value))
    elif role == "image":
        parts.append("imagine" if name else "imagine fără descriere")
    elif role == "list":
        parts.append(f"listă cu {node['list_size']} elemente" if node.get("list_size") is not None else "listă")
    elif role == "text":
        words = name.split()
        return " ".join(words[:12]) + ("..." if len(words) > 12 else "")
    else:
        label = {
            "banner": "reper antet", "navigation": "reper navigare",
            "main": "reper conținut principal", "contentinfo": "reper subsol",
            "search": "reper căutare", "form": "reper formular",
            "region": "regiune", "complementary": "reper complementar",
        }.get(role)
        if label is None:
            return ""
        parts.append(label)
    if states.get("required"):
        parts.append("obligatoriu")
    if states.get("disabled"):
        parts.append("indisponibil")
    if states.get("expanded") is True:
        parts.append("extins")
    elif states.get("expanded") is False:
        parts.append("restrâns")
    return ", ".join(parts)


def build_events(nodes: dict) -> dict:
    """Translates linear accessibility tree nodes into screen reader speech announcements."""
    ordered = sorted(nodes.get("nodes", []), key=lambda node: node["order"])
    candidates = []
    text_run = 0
    index = 0
    while index < len(ordered):
        position = index
        node = ordered[index]
        index += 1
        if node.get("role") == "text":
            names = [node.get("name") or ""]
            while (index < len(ordered) and ordered[index].get("role") == "text"
                   and ordered[index].get("parent") == node.get("parent")):
                names.append(ordered[index].get("name") or "")
                index += 1
            node = {**node, "name": " ".join(names)}
            text_run += 1
            if text_run > 2:
                continue
        else:
            text_run = 0
        speech = _speech(node)
        if speech:
            candidates.append((position, node, speech))

    # Reserve the introduction; overflow unnamed controls replace trailing static text.
    limit = max(1, MAX_EVENTS) - 1
    selected = candidates[:limit]
    for candidate in candidates[limit:]:
        position, node, _ = candidate
        if position >= 80:
            break
        if node.get("role") not in ("button", "link", "image", "textbox", "input") or (node.get("name") or "").strip():
            continue
        replacement = next((i for i in range(len(selected) - 1, -1, -1)
                            if selected[i][1].get("role") == "text"), None)
        if replacement is not None:
            selected.pop(replacement)
            selected.append(candidate)
    selected.sort(key=lambda candidate: candidate[0])
    events = [{"seq": 0, "node_id": None, "text": f"Pagina {nodes.get('title') or ''}".strip()}]
    events.extend({"seq": seq, "node_id": node["id"], "text": speech}
                  for seq, (_, node, speech) in enumerate(selected, start=1))
    return {"lang": "ro", "events": events}


if __name__ == "__main__":
    import json
    path = sys.argv[1] if len(sys.argv) > 1 else str(SAMPLES / "nodes.json")
    result = build_events(read_json(path))
    if len(sys.argv) > 2:
        write_json(Path(sys.argv[2]), result)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
