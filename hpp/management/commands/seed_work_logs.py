from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date
from hpp.models import Employee, Project, EmployeeWorkLog


class Command(BaseCommand):
    help = "Seed data aktivitas & kinerja harian karyawan"

    def handle(self, *args, **options):
        self.stdout.write("Memulai seeding kinerja karyawan...")

        emp1 = Employee.objects.filter(nik="EMP-001").first()  # Tukang Las
        emp2 = Employee.objects.filter(nik="EMP-002").first()  # Tukang Kayu
        emp3 = Employee.objects.filter(nik="EMP-003").first()  # Tukang Finishing
        emp6 = Employee.objects.filter(nik="EMP-006").first()  # Helper Perakitan

        p1 = Project.objects.filter(code="PRJ-2026-KNP01").first()
        p2 = Project.objects.filter(code="PRJ-2026-DSK02").first()

        today = date.today()

        logs = [
            {
                "employee": emp1,
                "project": p1,
                "date": today,
                "category": "Fabrikasi & Pengelasan",
                "task": "Pengelasan rangka utama kanopi besi hollow 40x80 dan pemasangan tiang penyangga.",
                "qty": Decimal("1"),
                "unit": "set rangka",
                "hours": Decimal("10"),
                "status": "completed",
                "obstacles": "Sempat hujan gerimis 30 menit pada siang hari.",
                "rating": 5,
            },
            {
                "employee": emp2,
                "project": p2,
                "date": today,
                "category": "Pemotongan & Perakitan Plywood",
                "task": "Pemotongan 10 lembar plywood meranti 18mm untuk top table meja modular.",
                "qty": Decimal("20"),
                "unit": "daun meja",
                "hours": Decimal("8"),
                "status": "completed",
                "obstacles": "",
                "rating": 4,
            },
            {
                "employee": emp3,
                "project": p2,
                "date": today,
                "category": "Finishing HPL & Edging",
                "task": "Pengeleman HPL woodgrain dan penempelan edging PVC pada 8 panel meja.",
                "qty": Decimal("8"),
                "unit": "panel",
                "hours": Decimal("8"),
                "status": "in_progress",
                "obstacles": "Menunggu lem kering sempurna sebelum perapihan tepi.",
                "rating": 4,
            },
            {
                "employee": emp6,
                "project": p2,
                "date": today,
                "category": "Perakitan & Packing",
                "task": "Pemasangan rel laci slow motion dan handle pintu laci mobile pedestal.",
                "qty": Decimal("12"),
                "unit": "laci",
                "hours": Decimal("9"),
                "status": "completed",
                "obstacles": "",
                "rating": 5,
            },
        ]

        for log in logs:
            if log["employee"]:
                EmployeeWorkLog.objects.create(
                    employee=log["employee"],
                    project=log["project"],
                    date=log["date"],
                    activity_category=log["category"],
                    task_description=log["task"],
                    output_qty=log["qty"],
                    output_unit=log["unit"],
                    hours_spent=log["hours"],
                    status=log["status"],
                    obstacles=log["obstacles"],
                    supervisor_rating=log["rating"],
                )

        self.stdout.write(self.style.SUCCESS("Seeding data kinerja karyawan selesai!"))
