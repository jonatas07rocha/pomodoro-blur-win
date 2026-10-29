import os
import re
import json
import requests

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# 1. Download lucide.ttf
ttf_path = os.path.join(ASSETS_DIR, "lucide.ttf")
print("Baixando lucide.ttf...")
r_ttf = requests.get("https://unpkg.com/lucide-static@latest/font/lucide.ttf", timeout=15)
with open(ttf_path, "wb") as f:
    f.write(r_ttf.content)
print(f"lucide.ttf salvo ({len(r_ttf.content)} bytes)")

# 2. Download and parse lucide.css
print("Baixando lucide.css e mapeando glifos...")
r_css = requests.get("https://unpkg.com/lucide-static@latest/font/lucide.css", timeout=15).text

mapping = {}
pattern = re.compile(r'\.icon-([a-zA-Z0-9_-]+)::before\s*\{\s*content:\s*"\\([0-9a-fA-F]+)"')
for match in pattern.finditer(r_css):
    name = match.group(1)
    code = int(match.group(2), 16)
    mapping[name] = chr(code)

json_path = os.path.join(ASSETS_DIR, "lucide_glyphs.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print(f"Salvos {len(mapping)} ícones Lucide no mapa!")
print("Exemplos:")
for k in ["play", "pause", "rotate-ccw", "skip-forward", "settings", "sparkles", "eye", "coffee", "brain", "check"]:
    print(f"  {k} -> \\u{ord(mapping[k]):04x} ({mapping.get(k)})")
