import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.test import Client
from hpp.models import Employee, AbsenceType, Attendance

def run_tests():
    print("==================================================")
    print("STARTING VERIFICATION: MASTER JENIS TIDAK MASUK")
    print("==================================================")

    # 1. Test Client HTTP Status
    client = Client()
    res_types = client.get("/absence-types/")
    assert res_types.status_code == 200, f"Expected 200 for /absence-types/, got {res_types.status_code}"
    print("[PASS] GET /absence-types/ returned 200 OK")

    res_att = client.get("/attendance/")
    assert res_att.status_code == 200, f"Expected 200 for /attendance/, got {res_att.status_code}"
    print("[PASS] GET /attendance/ returned 200 OK")

    # 2. Test Master Absence Type Creation
    test_code = "TEST_ISO"
    AbsenceType.objects.filter(code=test_code).delete()
    
    post_res = client.post("/absence-types/new/", {
        "code": test_code,
        "name": "Isolasi Mandiri / Karantina",
        "category": "SICK",
        "is_paid": "on",
        "wage_percentage": "75",
        "color": "amber",
        "requires_attachment": "on",
        "notes": "Protokol kesehatan karantina mandiri",
        "is_active": "on",
    })
    assert post_res.status_code == 302, f"Expected redirect 302, got {post_res.status_code}"
    
    iso_type = AbsenceType.objects.filter(code=test_code).first()
    assert iso_type is not None, "AbsenceType TEST_ISO was not created"
    assert iso_type.is_paid == True
    assert iso_type.wage_percentage == Decimal("75.00")
    print(f"[PASS] Created AbsenceType: {iso_type}")

    # 3. Test Attendance Calculation with Custom Absence Type
    emp = Employee.objects.first()
    if not emp:
        emp = Employee.objects.create(
            nik="EMP999",
            name="Testing Worker",
            position="Operator",
            daily_rate=Decimal("160000.00"),
            overtime_rate_per_hour=Decimal("25000.00"),
            is_active=True
        )
    test_date = date.today() + timedelta(days=50) # Future date to avoid collision
    Attendance.objects.filter(employee=emp, date=test_date).delete()

    # Create Attendance via POST
    post_att = client.post("/attendance/new/", {
        "employee_uuid": str(emp.uuid),
        "date": test_date.strftime("%Y-%m-%d"),
        "status": "TIDAK_HADIR",
        "absence_type_uuid": str(iso_type.uuid),
        "notes": "Karantina mandiri 3 hari",
    })
    assert post_att.status_code == 302, f"Expected redirect 302, got {post_att.status_code}"

    att = Attendance.objects.filter(employee=emp, date=test_date).first()
    assert att is not None, "Attendance record not found"
    assert att.absence_type == iso_type, "Attendance absence_type not linked correctly"
    assert att.display_status_label == iso_type.name
    
    expected_wage = emp.daily_rate * (Decimal("75.00") / Decimal(100))
    assert att.wage == expected_wage, f"Expected wage {expected_wage}, got {att.wage}"
    print(f"[PASS] Attendance calculated wage: Rp {att.wage} (Daily rate: {emp.daily_rate} * 75% = {expected_wage})")

    # 4. Test Delete Guard: Cannot delete AbsenceType while in use
    post_del_fail = client.post(f"/absence-types/{iso_type.uuid}/delete/")
    assert post_del_fail.status_code == 302
    # Object must still exist!
    assert AbsenceType.objects.filter(code=test_code).exists(), "Delete guard failed! In-use absence type was deleted!"
    print(f"[PASS] Delete Guard successfully blocked deletion of '{iso_type.name}' (in use by attendance record)")

    # 5. Test Update AbsenceType
    post_update = client.post(f"/absence-types/{iso_type.uuid}/update/", {
        "code": test_code,
        "name": "Isolasi Mandiri Revisi (80%)",
        "category": "SICK",
        "is_paid": "on",
        "wage_percentage": "80",
        "color": "amber",
        "is_active": "on",
    })
    assert post_update.status_code == 302
    iso_type.refresh_from_db()
    assert iso_type.name == "Isolasi Mandiri Revisi (80%)"
    assert iso_type.wage_percentage == Decimal("80.00")
    print(f"[PASS] Updated AbsenceType: {iso_type.name} to {iso_type.wage_percentage}%")

    # 6. Recalculate attendance wage on attendance save
    att.refresh_from_db()
    att.save()
    expected_wage_80 = emp.daily_rate * (Decimal("80.00") / Decimal(100))
    assert att.wage == expected_wage_80, f"Expected recalculated wage {expected_wage_80}, got {att.wage}"
    print(f"[PASS] Attendance wage recalculated on save: Rp {att.wage}")

    # 7. Cleanup test records & test deletion of unused absence type
    att.delete()
    post_del_success = client.post(f"/absence-types/{iso_type.uuid}/delete/")
    assert post_del_success.status_code == 302
    assert not AbsenceType.objects.filter(code=test_code).exists(), "Absence type should have been deleted"
    print(f"[PASS] Unused AbsenceType successfully deleted after attendance record removed")

    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (7/7)")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
