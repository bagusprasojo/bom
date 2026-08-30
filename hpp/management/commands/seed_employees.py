from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date, time
from hpp.models import Employee, Attendance


class Command(BaseCommand):
    help = "Seed data karyawan dan absensi harian"

    def handle(self, *args, **options):
        self.stdout.write("Memulai seeding karyawan & absensi...")

        employees_data = [
            {"nik": "EMP-001", "name": "Budi Santoso", "position": "Tukang Las Senior", "daily": Decimal("200000"), "ot": Decimal("30000")},
            {"nik": "EMP-002", "name": "Agus Prasetyo", "position": "Tukang Kayu Senior", "daily": Decimal("220000"), "ot": Decimal("35000")},
            {"nik": "EMP-003", "name": "Joko Widodo", "position": "Tukang Finishing HPL", "daily": Decimal("190000"), "ot": Decimal("28000")},
            {"nik": "EMP-004", "name": "Siti Rahma", "position": "Drafter & Estimator", "daily": Decimal("250000"), "ot": Decimal("40000")},
            {"nik": "EMP-005", "name": "Rian Hidayat", "position": "Helper / Kenek Las", "daily": Decimal("130000"), "ot": Decimal("20000")},
            {"nik": "EMP-006", "name": "Dedi Kurniawan", "position": "Helper Perakitan", "daily": Decimal("120000"), "ot": Decimal("20000")},
        ]

        created_emp = []
        for d in employees_data:
            emp, _ = Employee.objects.update_or_create(
                nik=d["nik"],
                defaults={
                    "name": d["name"],
                    "position": d["position"],
                    "daily_rate": d["daily"],
                    "overtime_rate_per_hour": d["ot"],
                    "is_active": True,
                }
            )
            created_emp.append(emp)

        # Buat absensi sample untuk hari ini & kemarin
        today = date.today()
        
        # Hari ini
        Attendance.objects.update_or_create(
            employee=created_emp[0], date=today,
            defaults={"status": "HADIR", "check_in": time(8, 0), "check_out": time(19, 0), "overtime_hours": Decimal("2"), "notes": "Lembur pengerjaan rangka"}
        )
        Attendance.objects.update_or_create(
            employee=created_emp[1], date=today,
            defaults={"status": "HADIR", "check_in": time(7, 55), "check_out": time(17, 0), "overtime_hours": Decimal("0"), "notes": "Hadir tepat waktu"}
        )
        Attendance.objects.update_or_create(
            employee=created_emp[2], date=today,
            defaults={"status": "IJIN", "check_in": None, "check_out": None, "overtime_hours": Decimal("0"), "notes": "Ijin urusan keluarga"}
        )
        Attendance.objects.update_or_create(
            employee=created_emp[3], date=today,
            defaults={"status": "HADIR", "check_in": time(8, 5), "check_out": time(17, 0), "overtime_hours": Decimal("0"), "notes": ""}
        )
        Attendance.objects.update_or_create(
            employee=created_emp[4], date=today,
            defaults={"status": "SAKIT", "check_in": None, "check_out": None, "overtime_hours": Decimal("0"), "notes": "Demam / flu"}
        )
        Attendance.objects.update_or_create(
            employee=created_emp[5], date=today,
            defaults={"status": "HADIR", "check_in": time(8, 0), "check_out": time(18, 0), "overtime_hours": Decimal("1"), "notes": "Lembur packing"}
        )

        self.stdout.write(self.style.SUCCESS(f"Seeding berhasil! {len(created_emp)} Karyawan dan absensi aktif."))
