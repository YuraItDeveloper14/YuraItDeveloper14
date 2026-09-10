# -*- coding: utf-8 -*-
"""Анімований термінальний рядок: фрази набираються по літері, по колу."""
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets") + os.sep
os.makedirs(OUT, exist_ok=True)

W, H = 980, 74
FS = 15.0
CW = FS * 0.6          # ширина моноширинного символу
X0 = 26                # лівий відступ промпту
XT = X0 + 34           # де починається сама фраза
BASE = 45              # базова лінія тексту

PHRASES = [
    "full-stack web applications",
    "desktop apps that ship as one file",
    "automations that run without me",
    "AI-assisted tools and agents",
    "B2B SaaS products",
    "APIs, dashboards, internal tools",
]

SLOT = 3.6             # секунд на фразу
TYPE = 1.3             # скільки триває набір
HOLD = 3.2             # доки фраза висить на екрані
TOTAL = SLOT * len(PHRASES)

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark":  dict(bg="#0d1117", border="#30363d", fg="#e6edf3", accent="#a78bfa", dim="#8b949e"),
    "light": dict(bg="#ffffff", border="#d0d7de", fg="#1f2328", accent="#7c3aed", dim="#59636e"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(theme):
    t = THEMES[theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{esc(" / ".join(PHRASES))}">',
           f'<style>text{{font-family:{MONO};}}</style>',
           f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" '
           f'fill="{t["bg"]}" stroke="{t["border"]}"/>',
           f'<text x="{X0}" y="{BASE}" font-size="{FS}" fill="{t["accent"]}">~ $</text>']

    for i, phrase in enumerate(PHRASES):
        w = len(phrase) * CW
        s0 = i * SLOT                       # старт вікна фрази
        k_start = s0 / TOTAL
        k_typed = (s0 + TYPE) / TOTAL
        k_hold = (s0 + HOLD) / TOTAL
        k_end = (s0 + SLOT) / TOTAL

        # групі вмикаємо видимість лише у її вікні
        kt = f"0;{k_start:.4f};{k_typed:.4f};{k_hold:.4f};{k_end:.4f};1"
        out.append(f'<g opacity="0">'
                   f'<animate attributeName="opacity" values="0;1;1;1;0;0" '
                   f'keyTimes="{kt}" dur="{TOTAL}s" repeatCount="indefinite" '
                   f'calcMode="discrete"/>')

        # маска, що розкриває текст зліва направо — ефект набору
        out.append(f'<clipPath id="clip{theme}{i}">'
                   f'<rect x="{XT}" y="0" width="0" height="{H}">'
                   f'<animate attributeName="width" values="0;0;{w:.1f};{w:.1f};{w:.1f};0" '
                   f'keyTimes="{kt}" dur="{TOTAL}s" repeatCount="indefinite" '
                   f'calcMode="linear"/></rect></clipPath>')
        out.append(f'<text x="{XT}" y="{BASE}" font-size="{FS}" fill="{t["fg"]}" '
                   f'clip-path="url(#clip{theme}{i})" xml:space="preserve">{esc(phrase)}</text>')

        # курсор їде за останньою набраною літерою
        out.append(f'<rect x="{XT}" y="{BASE-12}" width="9" height="16" fill="{t["accent"]}">'
                   f'<animate attributeName="x" values="{XT};{XT};{XT+w:.1f};{XT+w:.1f};{XT+w:.1f};{XT}" '
                   f'keyTimes="{kt}" dur="{TOTAL}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="1;1;0;0" dur="1s" '
                   f'repeatCount="indefinite"/></rect>')
        out.append('</g>')

    out.append('</svg>')
    return "\n".join(out)


for name in THEMES:
    p = OUT + "typing-" + name + ".svg"
    io.open(p, "w", encoding="utf-8").write(build(name))
    print("written", p, os.path.getsize(p), "bytes")
