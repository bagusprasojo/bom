import os
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import datetime

from hpp.models import (
    Customer, Project, BOMItem, ProjectLabor, ProjectOverhead,
    FinishedGood, ProjectFinishedGood, FinishedGoodStockMutation,
    Employee, Attendance, EmployeeWorkLog, BOMItemRealization, LaborRealization
)

class Command(BaseCommand):
    help = "Seeder data lengkap: Customer, Project (Single/Multi-Level BOM), Barang Jadi, Karyawan, Absensi, Log Kinerja & Realisasi"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Menjalankan seeder lengkap..."))

        # 1. CUSTOMERS
        c1, _ = Customer.objects.get_or_create(
            name="Bpk. Hendra Wijaya",
            defaults={
                "code": "CUST-001",
                "company_name": "PT Sentosa Abadi Jaya",
                "phone": "081234567890",
                "email": "hendra@sentosaabadi.com",
                "address": "Jl. Industri Raya No. 45, Surabaya",
                "notes": "Klien konstruksi baja & kanopi"
            }
        )

        c2, _ = Customer.objects.get_or_create(
            name="Ibu Ratna Sari",
            defaults={
                "code": "CUST-002",
                "company_name": "CV Citra Mandiri Desain",
                "phone": "081987654321",
                "email": "ratna@citramandiri.co.id",
                "address": "Jl. Ruko Kebon Jeruk Blok A2, Jakarta Barat",
                "notes": "Klien furnitur kantor"
            }
        )

        # 2. FINISHED GOODS
        fg1 = FinishedGood.objects.filter(name="Kursi Kerja Ergonomis Mesh Hitam (Hydraulic)").first()
        if not fg1:
            fg1 = FinishedGood.objects.create(
                sku="FG-CHAIR-01",
                name="Kursi Kerja Ergonomis Mesh Hitam (Hydraulic)",
                unit="unit",
                standard_cost=Decimal("450000.00"),
                current_stock=Decimal("50.00"),
                notes="Stok barang jadi siap pakai"
            )
            FinishedGoodStockMutation.objects.create(
                finished_good=fg1,
                mutation_type="IN",
                quantity=Decimal("50.00"),
                balance_after=Decimal("50.00"),
                reference_no="INIT-FG-01",
                notes="Saldo stock awal"
            )

        fg2 = FinishedGood.objects.filter(name="Partisi Aluminium Kaca Tempered 120x150cm").first()
        if not fg2:
            fg2 = FinishedGood.objects.create(
                sku="FG-PART-02",
                name="Partisi Aluminium Kaca Tempered 120x150cm",
                unit="panel",
                standard_cost=Decimal("750000.00"),
                current_stock=Decimal("20.00"),
                notes="Modul partisi siap pasang"
            )
            FinishedGoodStockMutation.objects.create(
                finished_good=fg2,
                mutation_type="IN",
                quantity=Decimal("20.00"),
                balance_after=Decimal("20.00"),
                reference_no="INIT-FG-02",
                notes="Saldo stock awal"
            )

        # 3. EMPLOYEES & ATTENDANCE
        emp1, _ = Employee.objects.get_or_create(
            nik="EMP-001",
            defaults={
                "name": "Agus Santoso",
                "position": "Kepala Tukang Las",
                "daily_rate": Decimal("150000.00"),
                "overtime_rate_per_hour": Decimal("25000.00"),
                "is_active": True,
            }
        )

        emp2, _ = Employee.objects.get_or_create(
            nik="EMP-002",
            defaults={
                "name": "Budi Hartono",
                "position": "Tukang Finishing",
                "daily_rate": Decimal("130000.00"),
                "overtime_rate_per_hour": Decimal("20000.00"),
                "is_active": True,
            }
        )

        today = datetime.date.today()
        Attendance.objects.get_or_create(
            employee=emp1,
            date=today,
            defaults={
                "status": "HADIR",
                "check_in": datetime.time(8, 0),
                "check_out": datetime.time(17, 0),
                "overtime_hours": Decimal("1.00"),
                "notes": "Hadir tepat waktu"
            }
        )

        # 4. PROJECT 1: SINGLE-LEVEL BOM
        p1, created1 = Project.objects.get_or_create(
            code="PRJ-202608-0001",
            defaults={
                "name": "Fabrikasi & Pasang Kanopi Besi Hollow 4x6m",
                "customer": c1,
                "customer_name": str(c1),
                "contract_value": Decimal("14500000.00"),
                "progress_percentage": 40,
                "status": "in_progress",
                "start_date": today - datetime.timedelta(days=5),
                "target_date": today + datetime.timedelta(days=10),
            }
        )

        if not p1.bom_items.exists():
            b1 = BOMItem.objects.create(
                project=p1,
                name="Besi Hollow Galvanis 40x40x1.8mm",
                item_type="material",
                unit="batang",
                est_qty=Decimal("12.00"),
                est_unit_cost=Decimal("135000.00"),
            )
            b2 = BOMItem.objects.create(
                project=p1,
                name="Atap Polycarbonate SolarFlat 3mm",
                item_type="material",
                unit="m2",
                est_qty=Decimal("24.00"),
                est_unit_cost=Decimal("210000.00"),
            )
            b3 = BOMItem.objects.create(
                project=p1,
                name="Cat Dasar Epoxy Anti Karat",
                item_type="material",
                unit="kaleng",
                est_qty=Decimal("3.00"),
                est_unit_cost=Decimal("95000.00"),
            )

            ProjectLabor.objects.create(
                project=p1,
                role_name="Tukang Las & Fabrikasi",
                unit="hari",
                est_quantity=Decimal("6.00"),
                est_rate=Decimal("150000.00"),
            )

            ProjectOverhead.objects.create(
                project=p1,
                name="Sewa Scaffolding & Transportasi Armada",
                est_cost=Decimal("650000.00"),
            )

            BOMItemRealization.objects.create(
                project=p1,
                bom_item=b1,
                date=today - datetime.timedelta(days=3),
                item_name=b1.name,
                unit=b1.unit,
                qty=Decimal("12.00"),
                unit_cost=Decimal("135000.00"),
                notes="Pembelian besi tahap 1"
            )

            LaborRealization.objects.create(
                project=p1,
                date=today - datetime.timedelta(days=2),
                role_name="Tukang Las & Fabrikasi",
                unit="hari",
                quantity=Decimal("3.00"),
                rate=Decimal("150000.00"),
                notes="Pengerjaan rangka kanopi 3 hari"
            )

        # 5. PROJECT 2: MULTI-LEVEL BOM
        p2, created2 = Project.objects.get_or_create(
            code="PRJ-202608-0002",
            defaults={
                "name": "Pengadaan 10 Set Workstation Meja Kubikal & Partisi",
                "customer": c2,
                "customer_name": str(c2),
                "contract_value": Decimal("38000000.00"),
                "progress_percentage": 20,
                "status": "in_progress",
                "start_date": today - datetime.timedelta(days=2),
                "target_date": today + datetime.timedelta(days=20),
            }
        )

        if not p2.bom_items.exists():
            sub1 = BOMItem.objects.create(
                project=p2,
                name="Sub-Assembly Rangka & Daun Meja",
                item_type="assembly",
                unit="set",
                est_qty=Decimal("10.00"),
            )
            BOMItem.objects.create(
                project=p2,
                parent=sub1,
                name="Multipleks Plywood 18mm",
                item_type="material",
                unit="lembar",
                est_qty=Decimal("8.00"),
                est_unit_cost=Decimal("245000.00"),
            )
            BOMItem.objects.create(
                project=p2,
                parent=sub1,
                name="HPL Taco Serat Kayu Natural",
                item_type="material",
                unit="lembar",
                est_qty=Decimal("10.00"),
                est_unit_cost=Decimal("185000.00"),
            )
            BOMItem.objects.create(
                project=p2,
                parent=sub1,
                name="Kaki Meja Besi Hollow 50x50 Powder Coating",
                item_type="material",
                unit="unit",
                est_qty=Decimal("20.00"),
                est_unit_cost=Decimal("160000.00"),
            )

            BOMItem.objects.create(
                project=p2,
                name="Handle & Aksesoris Grommet Kabel Meja",
                item_type="material",
                unit="set",
                est_qty=Decimal("10.00"),
                est_unit_cost=Decimal("75000.00"),
            )

            if fg1:
                ProjectFinishedGood.objects.create(
                    project=p2,
                    finished_good=fg1,
                    est_qty=Decimal("10.00"),
                    est_unit_cost=Decimal("450000.00"),
                )
            if fg2:
                ProjectFinishedGood.objects.create(
                    project=p2,
                    finished_good=fg2,
                    est_qty=Decimal("5.00"),
                    est_unit_cost=Decimal("750000.00"),
                )

            ProjectLabor.objects.create(
                project=p2,
                role_name="Tukang Kayu / Finishing HPL",
                unit="hari",
                est_quantity=Decimal("12.00"),
                est_rate=Decimal("140000.00"),
            )

            ProjectOverhead.objects.create(
                project=p2,
                name="Ongkos Kirim & Instalasi Lapangan",
                est_cost=Decimal("1200000.00"),
            )

            EmployeeWorkLog.objects.create(
                employee=emp1,
                project=p2,
                date=today,
                activity_category="Produksi",
                task_description="Pemotongan dan perakitan awal modul meja workstation",
                output_qty=Decimal("4.00"),
                output_unit="set",
                hours_spent=Decimal("8.00"),
                status="in_progress"
            )

        self.stdout.write(self.style.SUCCESS("Seeder berhasil dieksekusi lengkap!"))
