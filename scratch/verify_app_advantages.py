import os
import sys
import django

# Setup Django Environment
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from hpp import views

def run_tests():
    print("=== STARTING DEDICATED APP ADVANTAGES MENU VERIFICATION ===")

    # 1. Verify KEUNGGULAN_APLIKASI.md File
    print("\n--- TEST 1: KEUNGGULAN_APLIKASI.md File ---")
    adv_file = os.path.join(base_dir, "KEUNGGULAN_APLIKASI.md")
    assert os.path.exists(adv_file), "KEUNGGULAN_APLIKASI.md does not exist"
    with open(adv_file, "r", encoding="utf-8") as f:
        adv_content = f.read()
    assert len(adv_content) > 5000, "KEUNGGULAN_APLIKASI.md is too short"
    print(f"PASS: KEUNGGULAN_APLIKASI.md exists ({len(adv_content)} chars).")

    # 2. Verify URL Routing
    print("\n--- TEST 2: URL Routing for 'app_advantages' ---")
    url = reverse("app_advantages")
    assert url == "/keunggulan/", f"Expected '/keunggulan/', got '{url}'"
    resolved = resolve("/keunggulan/")
    assert resolved.func == views.app_advantages, "URL /keunggulan/ should resolve to views.app_advantages"
    print("PASS: Reverse and resolve for 'app_advantages' successful.")

    # 3. Verify View Rendering & Context
    print("\n--- TEST 3: View Rendering & Context ---")
    factory = RequestFactory()
    req = factory.get("/keunggulan/")
    resp = views.app_advantages(req)
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    
    html = resp.content.decode("utf-8")
    assert "Keunggulan Sistem HPP & Manufaktur" in html or "Keunggulan Sistem" in html, "Page title missing"
    assert "10 Keunggulan Utama" in html, "Features tab missing"
    assert "Matriks Perbandingan" in html, "Comparison tab missing"
    assert "Dampak Bisnis" in html, "Impact tab missing"
    assert "KEUNGGULAN_APLIKASI.md" in html, "Markdown tab missing"
    assert "Standard Costing vs Actual Costing" in html, "Advantage 1 missing"
    assert "Hierarchical BOM &amp; Multi-Level Sub-Assembly" in html or "Hierarchical BOM & Multi-Level Sub-Assembly" in html, "Advantage 2 missing"
    assert "Salin BOM" in html, "Advantage 3 missing"
    assert "Log Kinerja ke Realisasi" in html or "Log Kinerja" in html, "Advantage 4 missing"
    assert "Otomasi Gudang" in html, "Advantage 5 missing"
    assert "Multi-Satuan Konversi" in html, "Advantage 6 missing"
    assert "Penguncian Audit" in html, "Advantage 7 missing"
    assert "Keamanan Data" in html, "Advantage 8 missing"
    assert "Master Customer Interaktif" in html, "Advantage 9 missing"
    assert "Antarmuka Reaktif" in html, "Advantage 10 missing"
    assert "user-journey" in html, "Link to user journey missing"
    print("PASS: app_advantages view rendered successfully with 200 OK and all 10 advantages present.")

    # 4. Verify Sidebar Menu in base.html
    print("\n--- TEST 4: Sidebar Menu in base.html ---")
    base_html_path = os.path.join(base_dir, "hpp", "templates", "hpp", "base.html")
    with open(base_html_path, "r", encoding="utf-8") as f:
        base_html = f.read()
    assert "{% url 'app_advantages' %}" in base_html, "Sidebar base.html must have {% url 'app_advantages' %}"
    assert "Keunggulan Sistem" in base_html, "Sidebar must have label 'Keunggulan Sistem'"
    assert "10 Nilai" in base_html, "Sidebar must have badge '10 Nilai'"
    print("PASS: base.html sidebar has dedicated active link to app_advantages.")

    print("\n=== ALL APP ADVANTAGES MENU TESTS PASSED! ===")


if __name__ == "__main__":
    run_tests()
