import os
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import datetime

from hpp.models import (
    UnitMaster,
    Customer, Project, BOMItem, ProjectLabor, ProjectOverhead,
    FinishedGood, ProjectFinishedGood, FinishedGoodStockMutation,
    RawMaterial, RawMaterialUnitConversion, RawMaterialStockMutation,
    Employee, Attendance, EmployeeWorkLog, BOMItemRealization, LaborRealization
)

class Command(BaseCommand):
    help = "Seeder data lengkap: Customer, Bahan Baku Multi-Satuan, Project (Single/Multi-Level BOM), Barang Jadi, Karyawan, Absensi, Log Kinerja & Realisasi"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Menjalankan seeder lengkap..."))

        # 0. MASTER SATUAN (UNIT MASTER)
        default_units = [
            # Bahan Baku
            ("kg", "Kilogram", "raw_material", "Satuan berat standar"),
            ("gram", "Gram", "raw_material", "Satuan berat presisi"),
            ("meter", "Meter", "raw_material", "Satuan panjang"),
            ("batang", "Batang", "raw_material", "Profil baja, pipa, hollow (panjang 6m)"),
            ("lembar", "Lembar", "raw_material", "Plywood, plat, acrylic, gypsum"),
            ("roll", "Roll", "raw_material", "Kabel, kawat las, wallpaper, plastik"),
            ("kaleng", "Kaleng", "raw_material", "Cat, lem, thinner, cairan kimia"),
            ("liter", "Liter", "raw_material", "Cairan, oli, bensin"),
            ("m2", "Meter Persegi", "raw_material", "Luas bidang / karpet / atap"),
            ("m3", "Meter Kubik", "raw_material", "Volume kayu / cor / pasir"),
            ("dus", "Dus / Karton", "raw_material", "Kemasan packaging material"),
            ("ikat", "Ikat", "raw_material", "Besi beton, kawat"),
            ("pallet", "Pallet", "raw_material", "Kemasan muatan gudang"),
            ("pcs", "Pieces", "raw_material", "Baut, mur, fitting, aksesoris"),

            # Barang Jadi
            ("unit", "Unit", "finished_good", "Barang jadi mandiri"),
            ("set", "Set", "finished_good", "Perangkat / bundel barang jadi"),
            ("pcs", "Pieces (FG)", "finished_good", "Barang jadi satuan kecil"),
            ("box", "Box", "finished_good", "Kemasan box produk siap jual"),
            ("panel", "Panel", "finished_good", "Panel instrumen / partisi"),
            ("pack", "Pack", "finished_good", "Kemasan pack"),

            # Tenaga Kerja
            ("jam", "Jam Kerja", "labor", "Tarif per jam"),
            ("hari", "Hari Kerja", "labor", "Tarif per hari (8 jam)"),
            ("mandays", "Mandays / HOK", "labor", "Hari Orang Kerja"),
            ("titik", "Titik Instalasi", "labor", "Tarif borongan per titik lampu/stop kontak"),
            ("bulan", "Bulan", "labor", "Gaji/upah bulanan"),

            # Overhead / Biaya Lain
            ("paket", "Paket", "overhead", "Biaya lumpsum satu paket"),
            ("ls", "Lump Sum", "overhead", "Biaya borongan global"),
            ("trip", "Trip / Rit", "overhead", "Biaya pengiriman/transportasi"),
            ("kegiatan", "Kegiatan / Event", "overhead", "Biaya per aktivitas khusus"),
            ("bulan", "Bulan (Sewa)", "overhead", "Sewa alat bulanan"),
        ]

        for code, name, category, desc in default_units:
            UnitMaster.objects.get_or_create(
                code=code,
                category=category,
                defaults={"name": name, "description": desc, "is_active": True}
            )

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

        # 2. RAW MATERIALS (BAHAN BAKU) & MULTI-SATUAN
        rm1, _ = RawMaterial.objects.get_or_create(
            name="Besi Hollow Galvanis 40x40x1.8mm",
            defaults={
                "code": "MAT-0001",
                "category": "Besi & Baja",
                "stock_unit": "batang",
                "current_stock": Decimal("100.00"),
                "last_purchase_price": Decimal("135000.00"),
                "minimum_stock": Decimal("10.00"),
                "notes": "Panjang 6 meter per batang"
            }
        )
        if not rm1.mutations.exists():
            RawMaterialStockMutation.objects.create(
                raw_material=rm1,
                mutation_type="IN",
                input_qty=Decimal("100.00"),
                input_unit="batang",
                stock_qty=Decimal("100.00"),
                unit_price=Decimal("135000.00"),
                total_price=Decimal("13500000.00"),
                balance_after=Decimal("100.00"),
                reference_no="INIT-MAT-01",
                notes="Saldo stock awal"
            )

        # Konversi satuan: 1 IKAT = 10 BATANG
        RawMaterialUnitConversion.objects.get_or_create(
            raw_material=rm1,
            unit_name="ikat",
            defaults={
                "conversion_factor": Decimal("10.00"),
                "notes": "1 Ikat = 10 Batang"
            }
        )

        rm2, _ = RawMaterial.objects.get_or_create(
            name="Multipleks Plywood 18mm",
            defaults={
                "code": "MAT-0002",
                "category": "Kayu & Plywood",
                "stock_unit": "lembar",
                "current_stock": Decimal("50.00"),
                "last_purchase_price": Decimal("245000.00"),
                "minimum_stock": Decimal("5.00"),
                "notes": "Ukuran standar 122x244 cm"
            }
        )
        if not rm2.mutations.exists():
            RawMaterialStockMutation.objects.create(
                raw_material=rm2,
                mutation_type="IN",
                input_qty=Decimal("50.00"),
                input_unit="lembar",
                stock_qty=Decimal("50.00"),
                unit_price=Decimal("245000.00"),
                total_price=Decimal("12250000.00"),
                balance_after=Decimal("50.00"),
                reference_no="INIT-MAT-02",
                notes="Saldo stock awal"
            )

        # Konversi satuan: 1 PALLET = 50 LEMBAR
        RawMaterialUnitConversion.objects.get_or_create(
            raw_material=rm2,
            unit_name="pallet",
            defaults={
                "conversion_factor": Decimal("50.00"),
                "notes": "1 Pallet = 50 Lembar"
            }
        )

        # 3. FINISHED GOODS
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

        # 4. EMPLOYEES & ATTENDANCE
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

        # 5. PROJECT 1: SINGLE-LEVEL BOM
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

            # Sample Realisasi Bertahap untuk Project 1 (Auto Potong Stok Bahan Baku rm1)
            BOMItemRealization.objects.create(
                project=p1,
                bom_item=b1,
                raw_material=rm1,
                date=today - datetime.timedelta(days=3),
                item_name=b1.name,
                unit=b1.unit,
                qty=Decimal("12.00"),
                unit_cost=Decimal("135000.00"),
                notes="Pengambilan besi hollow dari gudang untuk kanopi"
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

        # 6. PROJECT 2: MULTI-LEVEL BOM
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

            if fg1:
                ProjectFinishedGood.objects.create(
                    project=p2,
                    finished_good=fg1,
                    est_qty=Decimal("10.00"),
                    est_unit_cost=Decimal("450000.00"),
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

        self.stdout.write(self.style.SUCCESS("Seeder berhasil dieksekusi lengkap!"))
