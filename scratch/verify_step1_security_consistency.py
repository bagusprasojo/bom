import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from hpp.models import Customer, RawMaterial, Employee, EmployeeWorkLog, Attendance, UnitMaster, Project
import hpp.views as views
import hpp.views_customer as views_customer
import hpp.views_raw_material as views_raw_material

rf = RequestFactory()

def add_messages_storage(request):
    setattr(request, "session", {})
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request

print("=== VERIFIKASI TAHAP 1: KEAMANAN & KONSISTENSI MENU ===")

# 1. Test Customer Delete (GET rejected, POST allowed when no projects)
cust_dummy = Customer.objects.create(code="CUST-TEST-999", name="Customer Test Keamanan")

# Test GET request
get_req = add_messages_storage(rf.get(f"/customers/{cust_dummy.uuid}/delete/"))
views_customer.customer_delete(get_req, cust_dummy.uuid)
assert Customer.objects.filter(uuid=cust_dummy.uuid).exists(), "FAIL: Customer deleted on GET!"
print("1.1 Customer Delete: GET ditolak dan data tetap aman (PASS)")

# Test POST request
post_req = add_messages_storage(rf.post(f"/customers/{cust_dummy.uuid}/delete/"))
views_customer.customer_delete(post_req, cust_dummy.uuid)
assert not Customer.objects.filter(uuid=cust_dummy.uuid).exists(), "FAIL: Customer not deleted on POST!"
print("1.2 Customer Delete: POST berhasil menghapus data tanpa project (PASS)")


# 2. Test Raw Material Delete (GET rejected, POST allowed when no mutations)
rm_dummy = RawMaterial.objects.create(code="RM-TEST-999", name="Bahan Test Keamanan", stock_unit="pcs")

# Test GET request
get_req = add_messages_storage(rf.get(f"/raw-materials/{rm_dummy.uuid}/delete/"))
views_raw_material.raw_material_delete(get_req, rm_dummy.uuid)
assert RawMaterial.objects.filter(uuid=rm_dummy.uuid).exists(), "FAIL: RawMaterial deleted on GET!"
print("2.1 Raw Material Delete: GET ditolak dan data tetap aman (PASS)")

# Test POST request
post_req = add_messages_storage(rf.post(f"/raw-materials/{rm_dummy.uuid}/delete/"))
views_raw_material.raw_material_delete(post_req, rm_dummy.uuid)
assert not RawMaterial.objects.filter(uuid=rm_dummy.uuid).exists(), "FAIL: RawMaterial not deleted on POST!"
print("2.2 Raw Material Delete: POST berhasil menghapus data tanpa mutasi (PASS)")


# 3. Test Employee Delete (Protected against attendances AND work_logs)
emp_dummy = Employee.objects.create(nik="EMP-TEST-999", name="Karyawan Test Log", daily_rate=150000)
work_log = EmployeeWorkLog.objects.create(
    employee=emp_dummy,
    date="2026-09-08",
    task_description="Tugas test proteksi",
    output_qty=1,
    output_unit="unit",
    hours_spent=8
)

# Test POST delete on employee with work_logs
post_req = add_messages_storage(rf.post(f"/employees/{emp_dummy.uuid}/delete/"))
views.employee_delete(post_req, emp_dummy.uuid)
assert Employee.objects.filter(uuid=emp_dummy.uuid).exists(), "FAIL: Employee deleted despite having work_logs!"
print("3.1 Employee Delete: Ditolak jika karyawan memiliki log kerja (PASS)")

# Clean up work log and test deletion
work_log.delete()
post_req = add_messages_storage(rf.post(f"/employees/{emp_dummy.uuid}/delete/"))
views.employee_delete(post_req, emp_dummy.uuid)
assert not Employee.objects.filter(uuid=emp_dummy.uuid).exists(), "FAIL: Employee not deleted after work_log cleanup!"
print("3.2 Employee Delete: Berhasil dihapus setelah bersih dari log kerja & absensi (PASS)")


# 4. Test Sidebar URLs in base.html
base_path = "hpp/templates/hpp/base.html"
with open(base_path, "r", encoding="utf-8") as f:
    base_html = f.read()

assert "{% url 'unit_list' %}" in base_html, "FAIL: unit_list not found in base.html"
assert 'href="/units/"' not in base_html, "FAIL: hardcoded /units/ still found in base.html"
assert "{% url 'finished_good_mutation_list' %}" in base_html, "FAIL: finished_good_mutation_list not found in base.html"
assert "{% url 'finished_good_stock_card_index' %}" in base_html, "FAIL: finished_good_stock_card_index not found in base.html"
print("4.1 Sidebar base.html: Tautan Master Satuan & Barang Jadi terseragamkan (PASS)")


# 5. Test Work Log List context & template datalist
req = add_messages_storage(rf.get("/work-logs/"))
response = views.work_log_list(req)
assert response.status_code == 200, f"FAIL: status {response.status_code}"
assert b"outputUnitsList" in response.content, "FAIL: outputUnitsList not in response HTML"

with open("hpp/templates/hpp/work_log_list.html", "r", encoding="utf-8") as f:
    wl_html = f.read()

assert 'list="outputUnitsList"' in wl_html, "FAIL: list='outputUnitsList' not found in work_log_list.html"
assert '<datalist id="outputUnitsList">' in wl_html, "FAIL: datalist not found in work_log_list.html"
print("5.1 Work Log UI: Datalist UnitMaster terpasang pada modal Add & Edit (PASS)")

print("\nSELURUH 5 PENGUJIAN TAHAP 1 BERHASIL DILAKUKAN DENGAN SEMPURNA!")
