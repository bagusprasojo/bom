import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.test import Client
from hpp.models import Employee, Project, AbsenceType, Attendance, EmployeeWorkLog, LaborRealization

def run_tests():
    print("==================================================")
    print("STARTING VERIFICATION: WORK LOGS UPGRADES (1-4)")
    print("==================================================")

    client = Client()

    # 1. Test GET /work-logs/
    res = client.get("/work-logs/")
    assert res.status_code == 200, f"Expected 200 OK, got {res.status_code}"
    print("[PASS] 1. GET /work-logs/ returned 200 OK")

    # Setup test employee and project
    emp = Employee.objects.first()
    if not emp:
        emp = Employee.objects.create(
            nik="EMP-TEST",
            name="Testing Worker",
            position="Tukang Kayu",
            daily_rate=Decimal("160000.00"),
            overtime_rate_per_hour=Decimal("25000.00")
        )
    
    project = Project.objects.filter(status="in_progress").first()
    if not project:
        project = Project.objects.create(
            name="Project Uji Kinerja",
            code="PRJ-WL-TEST",
            contract_value=Decimal("50000000"),
            status="in_progress"
        )

    test_date = date.today() + timedelta(days=60)

    # 2. Test Cross-Validation with Attendance (Absent Employee)
    abs_type = AbsenceType.objects.filter(code="CT").first()
    att, _ = Attendance.objects.update_or_create(
        employee=emp,
        date=test_date,
        defaults={
            "status": "TIDAK_HADIR",
            "absence_type": abs_type,
        }
    )

    # Create Work Log for this absent date
    post_res = client.post("/work-logs/new/", {
        "employee_uuid": str(emp.uuid),
        "project_uuid": str(project.uuid),
        "date": test_date.strftime("%Y-%m-%d"),
        "activity_category": "Perakitan & Konstruksi (Assembly)",
        "task_description": "Perakitan rangka meja rapat kayu jati",
        "output_qty": "2",
        "output_unit": "unit",
        "hours_spent": "8",
        "status": "completed",
        "supervisor_rating": "5",
        "obstacles": "Tidak ada kendala",
    }, follow=True)
    assert post_res.status_code == 200
    
    # Check that warning message about attendance was raised
    from django.contrib.messages import get_messages
    messages = list(get_messages(post_res.wsgi_request))
    has_warning = any("Pemberitahuan Presensi" in m.message for m in messages)
    assert has_warning, f"Expected attendance cross-validation warning in messages, got: {[m.message for m in messages]}"
    print(f"[PASS] 2. Attendance cross-validation triggered warning for employee {emp.name} ({att.display_status_label})")

    log = EmployeeWorkLog.objects.filter(employee=emp, date=test_date).first()
    assert log is not None, "Work log was not created"
    assert log.project == project

    # 3. Test Excel Export
    res_excel = client.get("/work-logs/export/?q=Perakitan")
    assert res_excel.status_code == 200
    assert "spreadsheetml" in res_excel["Content-Type"], f"Unexpected Content-Type: {res_excel['Content-Type']}"
    assert len(res_excel.content) > 1000, "Export file content is too small"
    print(f"[PASS] 3. GET /work-logs/export/ successfully returned Excel workbook ({len(res_excel.content)} bytes)")

    # 4. Test Post to Project Labor Realization
    suggested_rate = log.suggested_hourly_rate
    assert suggested_rate == round(emp.daily_rate / Decimal(8), 2)

    post_realize_res = client.post(f"/work-logs/{log.uuid}/post-realization/", {
        "rate": str(suggested_rate),
        "role_name": f"{emp.position} ({emp.name})",
        "is_additional": "on",
        "notes": "Posting otomatis pengujian log kinerja",
    }, follow=True)
    assert post_realize_res.status_code == 200

    log.refresh_from_db()
    assert log.labor_realization is not None, "labor_realization was not linked to work log"
    realization = log.labor_realization
    expected_cost = Decimal("8") * suggested_rate
    assert realization.total_cost == expected_cost, f"Expected cost {expected_cost}, got {realization.total_cost}"
    assert realization.project == project
    print(f"[PASS] 4. Post to HPP Realization succeeded: Rp {realization.total_cost} linked to project {project.code}")

    # 5. Test Audit Lock: Completed project prevents posting or unposting
    old_status = project.status
    project.status = "completed"
    project.save()

    # Try unposting on closed project
    unpost_closed_res = client.post(f"/work-logs/{log.uuid}/unpost-realization/", follow=True)
    messages_closed = list(get_messages(unpost_closed_res.wsgi_request))
    has_lock_err = any("Audit Locked" in m.message for m in messages_closed)
    assert has_lock_err, "Audit lock failed to block unposting on completed project"
    print(f"[PASS] 5. Audit Lock correctly blocked modifying realization on completed project")

    # Restore project status & test unpost
    project.status = old_status
    project.save()

    unpost_res = client.post(f"/work-logs/{log.uuid}/unpost-realization/", follow=True)
    assert unpost_res.status_code == 200
    log.refresh_from_db()
    assert log.labor_realization is None, "labor_realization was not unlinked on unpost"
    assert not LaborRealization.objects.filter(id=realization.id).exists(), "LaborRealization was not deleted"
    print(f"[PASS] 6. Unpost cleanly detached realization and deleted LaborRealization record")

    # Cleanup
    log.delete()
    att.delete()
    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (6/6)")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
