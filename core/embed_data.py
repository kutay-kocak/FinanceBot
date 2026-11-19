#!/usr/bin/env python3
"""
embed_data.py - latest_analysis.json dosyasını web/index.html, public/index.html ve index.html içine gömer.
Böylece tarayıcı sayfayı açtığında ağ isteği beklemeden 0 milisaniyede tüm portföy ve analizleri gösterir.
"""

import os
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.dirname(os.path.abspath(__file__)).endswith("core") else os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "latest_analysis.json")

def embed():
    if not os.path.exists(DATA_FILE):
        print("data/latest_analysis.json bulunamadi.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        json_str = f.read().strip()

    # JSON geçerlilik testi
    json.loads(json_str)

    html_files = [
        os.path.join(BASE_DIR, "web", "index.html"),
        os.path.join(BASE_DIR, "public", "index.html"),
        os.path.join(BASE_DIR, "index.html")
    ]

    pattern = re.compile(r'(<script id="embedded-analysis-data" type="application/json">)([\s\S]*?)(</script>)')

    for h_path in html_files:
        if not os.path.exists(h_path):
            continue
        with open(h_path, "r", encoding="utf-8") as f:
            content = f.read()

        if pattern.search(content):
            new_content = pattern.sub(rf'\g<1>\n{json_str}\n\g<3>', content)
        else:
            # Etiket henüz yoksa </body> öncesine ekle
            replacement = f'\n  <script id="embedded-analysis-data" type="application/json">\n{json_str}\n  </script>\n</body>'
            new_content = content.replace('</body>', replacement)

        with open(h_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[OK] {os.path.relpath(h_path, BASE_DIR)} güncellendi ({len(new_content)} bayt).")

if __name__ == "__main__":
    embed()
