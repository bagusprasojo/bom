# hpp/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date
from hpp.models import Project, BOMItem, ProjectLabor, ProjectOverhead


class Command(BaseCommand):
    help = "Seed database dengan 2 project nyata (Single-level dan Multi-level BOM)"

    def handle(self, *args, **options):
        self.stdout.write("Memulai seeding data...")

        # -------------------------------------------------------------------------
        # PROJECT 1: SINGLE-LEVEL BOM (Pemasangan Kanopi Minimalis Rumah Tinggal)
        # -------------------------------------------------------------------------
        p1, _ = Project.objects.update_or_create(
            code="PRJ-2026-KNP01",
            defaults={
                "name": "Fabrikasi & Pasang Kanopi Besi Hollow 4x6m",
                "customer_name": "Bpk. Hendra Gunawan",
                "contract_value": Decimal("14500000"),
                "status": "in_progress",
                "progress_percentage": 75,
                "start_date": date(2026, 8, 10),
                "target_date": date(2026, 9, 5),
            }
        )
        p1.bom_items.all().delete()
        p1.labor_items.all().delete()
        p1.overhead_items.all().delete()

        # Material Single-level
        materials_p1 = [
            {"name": "Besi Hollow Galvanis 40x80x2mm", "unit": "batang", "eqty": 8, "ecost": 235000, "aqty": 8, "acost": 240000},
            {"name": "Besi Hollow Galvanis 40x40x1.8mm", "unit": "batang", "eqty": 12, "ecost": 145000, "aqty": 13, "acost": 145000},
            {"name": "Atap Polycarbonate SolarTuff 3mm", "unit": "lembar", "eqty": 8, "ecost": 420000, "aqty": 8, "acost": 420000},
            {"name": "Baut Roofing & Dynabolt M10", "unit": "pack", "eqty": 2, "ecost": 85000, "aqty": 2, "acost": 90000},
            {"name": "Cat Epoxy Primer & Cat Finishing Hitam Doff", "unit": "kaleng", "eqty": 4, "ecost": 125000, "aqty": 4, "acost": 130000},
            {"name": "Kawat Las RD-260 2.6mm", "unit": "dus", "eqty": 2, "ecost": 110000, "aqty": 2, "acost": 110000},
        ]
        for m in materials_p1:
            BOMItem.objects.create(
                project=p1,
                item_type="material",
                name=m["name"],
                unit=m["unit"],
                est_qty=Decimal(m["eqty"]),
                est_unit_cost=Decimal(m["ecost"]),
                act_qty=Decimal(m["aqty"]),
                act_unit_cost=Decimal(m["acost"]),
            )

        # Labor Single-level
        labors_p1 = [
            {"role": "Tukang Las Senior", "unit": "hari", "eqty": 6, "erate": 200000, "aqty": 6, "arate": 200000},
            {"role": "Kenek / Pembantu Tukang", "unit": "hari", "eqty": 6, "erate": 130000, "aqty": 7, "arate": 130000},
        ]
        for l in labors_p1:
            ProjectLabor.objects.create(
                project=p1,
                role_name=l["role"],
                unit=l["unit"],
                est_quantity=Decimal(l["eqty"]),
                est_rate=Decimal(l["erate"]),
                act_quantity=Decimal(l["aqty"]),
                act_rate=Decimal(l["arate"]),
            )

        # Overhead Single-level
        ProjectOverhead.objects.create(project=p1, name="Sewa Mobil Pick-up & Transportasi", est_cost=Decimal(450000), act_cost=Decimal(500000))
        ProjectOverhead.objects.create(project=p1, name="Konsumsi Harian Tukang (6 hari)", est_cost=Decimal(360000), act_cost=Decimal(420000))

        # -------------------------------------------------------------------------
        # PROJECT 2: MULTI-LEVEL BOM (Produksi Meja Kerja Kantor Modular)
        # -------------------------------------------------------------------------
        p2, _ = Project.objects.update_or_create(
            code="PRJ-2026-DSK02",
            defaults={
                "name": "Pengadaan 20 Unit Modular Executive Desk 160x80cm",
                "customer_name": "PT Sinergi Nusantara Perkasa",
                "contract_value": Decimal("48000000"),
                "status": "in_progress",
                "progress_percentage": 40,
                "start_date": date(2026, 8, 15),
                "target_date": date(2026, 9, 20),
            }
        )
        p2.bom_items.all().delete()
        p2.labor_items.all().delete()
        p2.overhead_items.all().delete()

        # SUB-ASSEMBLY 1: Top Table & Panel
        sub1 = BOMItem.objects.create(
            project=p2,
            item_type="assembly",
            name="Sub-Assembly: Top Table & Partisi Depan",
            unit="unit",
        )
        BOMItem.objects.create(project=p2, parent=sub1, item_type="material", name="Plywood Meranti 18mm", unit="lembar", est_qty=Decimal(10), est_unit_cost=Decimal(265000), act_qty=Decimal(11), act_unit_cost=Decimal(265000))
        BOMItem.objects.create(project=p2, parent=sub1, item_type="material", name="HPL Woodgrain Matte Finish", unit="lembar", est_qty=Decimal(14), est_unit_cost=Decimal(185000), act_qty=Decimal(14), act_unit_cost=Decimal(190000))
        BOMItem.objects.create(project=p2, parent=sub1, item_type="material", name="Lem Kuning High Bond 10kg", unit="blek", est_qty=Decimal(3), est_unit_cost=Decimal(340000), act_qty=Decimal(3), act_unit_cost=Decimal(340000))
        BOMItem.objects.create(project=p2, parent=sub1, item_type="material", name="Edging PVC 1mm x 42mm", unit="roll", est_qty=Decimal(2), est_unit_cost=Decimal(220000), act_qty=Decimal(2), act_unit_cost=Decimal(220000))

        # SUB-ASSEMBLY 2: Rangka Kaki Besi Powder Coating
        sub2 = BOMItem.objects.create(
            project=p2,
            item_type="assembly",
            name="Sub-Assembly: Rangka Kaki Besi & Beam",
            unit="unit",
        )
        BOMItem.objects.create(project=p2, parent=sub2, item_type="material", name="Pipa Besi Hollow Kotak 50x50x2mm", unit="batang", est_qty=Decimal(16), est_unit_cost=Decimal(290000), act_qty=Decimal(16), act_unit_cost=Decimal(295000))
        BOMItem.objects.create(project=p2, parent=sub2, item_type="material", name="Plat Besi Dudukan Kaki 3mm", unit="lembar", est_qty=Decimal(2), est_unit_cost=Decimal(380000), act_qty=Decimal(2), act_unit_cost=Decimal(380000))
        BOMItem.objects.create(project=p2, parent=sub2, item_type="material", name="Jasa Finishing Powder Coating White", unit="lot", est_qty=Decimal(1), est_unit_cost=Decimal(3200000), act_qty=Decimal(1), act_unit_cost=Decimal(3200000))

        # SUB-ASSEMBLY 3: Mobile Pedestal / Laci 3 Susun
        sub3 = BOMItem.objects.create(
            project=p2,
            item_type="assembly",
            name="Sub-Assembly: Mobile Drawer Laci 3 Susun",
            unit="unit",
        )
        BOMItem.objects.create(project=p2, parent=sub3, item_type="material", name="Plywood Meranti 12mm", unit="lembar", est_qty=Decimal(8), est_unit_cost=Decimal(195000), act_qty=Decimal(8), act_unit_cost=Decimal(195000))
        BOMItem.objects.create(project=p2, parent=sub3, item_type="material", name="Rel Laci Slow-motion 40cm", unit="set", est_qty=Decimal(60), est_unit_cost=Decimal(45000), act_qty=Decimal(60), act_unit_cost=Decimal(48000))
        BOMItem.objects.create(project=p2, parent=sub3, item_type="material", name="Kunci Central Lock 3 Susun", unit="set", est_qty=Decimal(20), est_unit_cost=Decimal(38000), act_qty=Decimal(20), act_unit_cost=Decimal(38000))
        BOMItem.objects.create(project=p2, parent=sub3, item_type="material", name="Handle Aluminium Minimalis", unit="pcs", est_qty=Decimal(60), est_unit_cost=Decimal(15000), act_qty=Decimal(60), act_unit_cost=Decimal(15000))
        BOMItem.objects.create(project=p2, parent=sub3, item_type="material", name="Roda Kaster Nylon Laci 2 inch", unit="set", est_qty=Decimal(20), est_unit_cost=Decimal(28000), act_qty=Decimal(20), act_unit_cost=Decimal(28000))

        # Labor Multi-level
        labors_p2 = [
            {"role": "Tukang Kayu Interior Senior", "unit": "hari", "eqty": 24, "erate": 220000, "aqty": 12, "arate": 220000},
            {"role": "Tukang Las & Fitting Besi", "unit": "hari", "eqty": 16, "erate": 200000, "aqty": 16, "arate": 200000},
            {"role": "Tukang Finishing HPL & Edging", "unit": "hari", "eqty": 20, "erate": 190000, "aqty": 10, "arate": 190000},
            {"role": "Helper / Perakitan", "unit": "hari", "eqty": 30, "erate": 120000, "aqty": 15, "arate": 120000},
        ]
        for l in labors_p2:
            ProjectLabor.objects.create(
                project=p2,
                role_name=l["role"],
                unit=l["unit"],
                est_quantity=Decimal(l["eqty"]),
                est_rate=Decimal(l["erate"]),
                act_quantity=Decimal(l["aqty"]),
                act_rate=Decimal(l["arate"]),
            )

        # Overhead Multi-level
        ProjectOverhead.objects.create(project=p2, name="Listrik Workshop & Pemakaian Mesin", est_cost=Decimal(1200000), act_cost=Decimal(950000))
        ProjectOverhead.objects.create(project=p2, name="Packing Kardus + Bubble Wrap (20 Meja)", est_cost=Decimal(850000), act_cost=Decimal(900000))
        ProjectOverhead.objects.create(project=p2, name="Ongkos Kirim Truk CDD & Bongkar Muat Lokasi", est_cost=Decimal(1500000), act_cost=Decimal(1500000))

        self.stdout.write(self.style.SUCCESS("Seeding berhasil! 2 project siap diuji."))
