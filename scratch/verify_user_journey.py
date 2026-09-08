import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from django.test import RequestFactory
from django.urls import reverse, resolve
from hpp import views


def run_tests():
    print("=== STARTING USER JOURNEY VERIFICATION ===")

    # 1. Verify USER_JOURNEY.md File Existence & Content
    print("\n--- TEST 1: USER_JOURNEY.md File ---")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, "USER_JOURNEY.md")
    assert os.path.exists(md_path), f"File {md_path} does not exist!"
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_keywords = [
        "Panduan Alur Pengguna",
        "Siklus Utama Proyek",
        "Inisiasi & Pembuatan Proyek Baru",
        "Bill of Materials (BOM)",
        "Tenaga Kerja",
        "Biaya Overhead",
        "Barang Jadi",
        "Realisasi",
        "Closing Proyek",
        "Berita Acara",
        "Master Customer",
        "Master Satuan",
        "Master Bahan Baku",
        "SDM, Presensi & Log Kinerja",
        "Pergudangan & Kartu Stok",
        "Matriks Peran"
    ]
    for kw in required_keywords:
        assert kw.lower() in content.lower(), f"Missing required keyword: '{kw}' in USER_JOURNEY.md"
    print(f"PASS: USER_JOURNEY.md exists ({len(content)} chars) and contains all required sections.")

    # 1b. Verify KEUNGGULAN_APLIKASI.md File Existence & Content
    print("\n--- TEST 1b: KEUNGGULAN_APLIKASI.md File ---")
    adv_path = os.path.join(base_dir, "KEUNGGULAN_APLIKASI.md")
    assert os.path.exists(adv_path), f"File {adv_path} does not exist!"
    with open(adv_path, "r", encoding="utf-8") as f:
        adv_content = f.read()
    
    adv_keywords = [
        "Keunggulan & Nilai Strategis Aplikasi",
        "10 Keunggulan Utama",
        "Standard Costing vs Actual Costing",
        "Hierarchical Bill of Materials (BOM)",
        "Salin BOM dari Proyek Lain",
        "Log Kinerja",
        "Otomasi Gudang",
        "Multi-Satuan",
        "Penguncian Data Audit",
        "Reopen",
        "Safeguard",
        "Matriks Perbandingan"
    ]
    for kw in adv_keywords:
        assert kw.lower() in adv_content.lower(), f"Missing required keyword: '{kw}' in KEUNGGULAN_APLIKASI.md"
    print(f"PASS: KEUNGGULAN_APLIKASI.md exists ({len(adv_content)} chars) and contains all 10 key advantages.")

    # 2. Verify URL Reverse & Resolving
    print("\n--- TEST 2: URL Routing ---")
    url = reverse("user_journey")
    assert url == "/user-journey/", f"Expected '/user-journey/', got '{url}'"
    resolved = resolve("/user-journey/")
    assert resolved.func == views.user_journey, "URL /user-journey/ should resolve to views.user_journey"
    print("PASS: Reverse and resolve for 'user_journey' successful.")

    # 3. Verify View Response & HTML Rendering
    print("\n--- TEST 3: View Rendering & Context ---")
    factory = RequestFactory()
    req = factory.get("/user-journey/")
    resp = views.user_journey(req)
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    
    html = resp.content.decode("utf-8")
    assert "Panduan Alur Pengguna" in html, "Page title/header missing"
    assert "Siklus Utama Proyek" in html, "Lifecycle tab missing"
    assert "Modul Pendukung" in html, "Supporting modules tab missing"
    assert "Keunggulan Sistem" in html or "Keunggulan Aplikasi" in html, "Advantages tab missing"
    assert "Dokumen USER_JOURNEY.md" in html or "USER_JOURNEY.md" in html, "Markdown tab missing"
    assert "User Journey &amp; Alur" in html or "User Journey & Alur" in html, "Sidebar menu item missing"
    assert "KEUNGGULAN_APLIKASI.md" in html, "KEUNGGULAN_APLIKASI.md mention missing"
    
    # Check that journey steps are rendered
    assert "Inisiasi" in html and "Pembuatan Proyek Baru" in html
    assert "Alokasi Barang Jadi" in html or "Barang Jadi" in html
    assert "Closing Proyek" in html
    assert "Berita Acara (BAP)" in html or "Berita Acara" in html
    print("PASS: user_journey view rendered successfully with 200 OK and all components present.")

    # 4. Verify Sidebar Menu in base.html
    print("\n--- TEST 4: Sidebar Menu in base.html ---")
    base_html_path = os.path.join(base_dir, "hpp", "templates", "hpp", "base.html")
    with open(base_html_path, "r", encoding="utf-8") as f:
        base_html = f.read()
    assert "{% url 'user_journey' %}" in base_html, "Sidebar base.html must have {% url 'user_journey' %}"
    assert "User Journey & Alur" in base_html, "Sidebar must have label 'User Journey & Alur'"
    print("PASS: base.html sidebar has active link to user_journey.")

    print("\n=== ALL USER JOURNEY VERIFICATION TESTS PASSED! ===")


if __name__ == "__main__":
    run_tests()
