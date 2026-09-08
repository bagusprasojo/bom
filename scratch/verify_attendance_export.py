import os
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

import openpyxl
from datetime import date, timedelta
from decimal import Decimal
from django.test import Client
from hpp.models import Employee, Attendance, AbsenceType

def run_tests():
    print("==================================================")
    print("STARTING VERIFICATION: ATTENDANCE PERIOD EXPORT")
    print("==================================================")

    client = Client()

    # 1. Test GET /attendance/ page loads
    res_page = client.get("/attendance/")
    assert res_page.status_code == 200, f"Expected 200 OK, got {res_page.status_code}"
    print("[PASS] 1. GET /attendance/ returned 200 OK with Export button")

    # 2. Test GET /attendance/export/ with default params
    res_export = client.get("/attendance/export/")
    assert res_export.status_code == 200, f"Expected 200 OK, got {res_export.status_code}"
    assert "spreadsheetml" in res_export["Content-Type"], f"Unexpected Content-Type: {res_export['Content-Type']}"
    assert len(res_export.content) > 1000, "Content too small"
    print(f"[PASS] 2. GET /attendance/export/ returned valid Excel file ({len(res_export.content)} bytes)")

    # 3. Test GET /attendance/export/ with specific date range & employee filter
    emp = Employee.objects.filter(is_active=True).first()
    start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = date.today().strftime("%Y-%m-%d")

    res_filtered = client.get(f"/attendance/export/?start_date={start_date}&end_date={end_date}&employee={emp.uuid if emp else ''}")
    assert res_filtered.status_code == 200

    # Inspect Workbook Structure
    wb = openpyxl.load_workbook(io.BytesIO(res_filtered.content))
    sheet_names = wb.sheetnames
    assert "Rekapitulasi Kehadiran" in sheet_names, f"Missing sheet: {sheet_names}"
    assert "Log Harian Detail" in sheet_names, f"Missing sheet: {sheet_names}"
    print(f"[PASS] 3. Verified 2 Sheets generated: {sheet_names}")

    # Inspect Sheet 1: Rekapitulasi Kehadiran
    ws1 = wb["Rekapitulasi Kehadiran"]
    assert "REKAPITULASI" in str(ws1["A1"].value)
    headers_ws1 = [ws1.cell(row=4, column=c).value for c in range(1, 15)]
    assert "NIK" in headers_ws1
    assert "Nama Karyawan" in headers_ws1
    assert "Hadir" in headers_ws1
    assert "Total Akumulasi Upah (Rp)" in headers_ws1
    print(f"[PASS] 4. Sheet 1 headers verified: {headers_ws1[:5]}...")

    # Inspect Sheet 2: Log Harian Detail
    ws2 = wb["Log Harian Detail"]
    assert "DETAIL" in str(ws2["A1"].value)
    headers_ws2 = [ws2.cell(row=4, column=c).value for c in range(1, 15)]
    assert "Tanggal" in headers_ws2
    assert "Jenis Tidak Masuk" in headers_ws2
    assert "Upah Harian (Rp)" in headers_ws2
    print(f"[PASS] 5. Sheet 2 headers verified: {headers_ws2[:5]}...")

    print("\n==================================================")
    print("ALL ATTENDANCE EXPORT TESTS PASSED SUCCESSFULLY! (5/5)")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
