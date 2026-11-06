(el) => {
  if (el && el.nodeType === 3) el = el.parentElement;
  if (!el || el.nodeType !== 1) return null;
  const uniqueId = (e) => e.id && document.querySelectorAll('#' + CSS.escape(e.id)).length === 1;
  const parts = [];
  let cur = el;
  while (cur && cur.nodeType === 1 && cur !== document.documentElement) {
    if (uniqueId(cur)) { parts.unshift('#' + CSS.escape(cur.id)); return parts.join(' > '); }
    const tag = cur.tagName.toLowerCase();
    let i = 1, sib = cur;
    while ((sib = sib.previousElementSibling)) if (sib.tagName === cur.tagName) i++;
    parts.unshift(tag + ':nth-of-type(' + i + ')');
    cur = cur.parentElement;
  }
  parts.unshift('html');
  return parts.join(' > ');
}
