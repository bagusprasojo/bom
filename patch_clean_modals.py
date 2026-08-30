with open("hpp/templates/hpp/project_detail.html", "r", encoding="utf-8-sig") as f:
    text = f.read()

import re

# Cari dan bersihkan bagian field realisasi di modal-modal project_detail.html
# 1. Hapus div section "Realisasi Lapangan (Opsional)" pada Add/Edit BOM
text = re.sub(
    r'<div class="pt-2 border-t border-slate-100">\s*<h4 class="text-xs font-bold text-slate-700 uppercase mb-2">Realisasi Lapangan \(Opsional\)</h4>.*?</div>\s*</div>\s*</div>\s*(?=<div class="flex justify-end)',
    '',
    text,
    flags=re.DOTALL
)

with open("hpp/templates/hpp/project_detail.html", "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

print("Pass 1 done")
