from django.core.management.base import BaseCommand
from decimal import Decimal
from hpp.models import FinishedGood, FinishedGoodStockMutation


class Command(BaseCommand):
    help = "Seed master barang jadi lengkap dengan saldo stock awal dan riwayat mutasi"

    def handle(self, *args, **options):
        self.stdout.write("Memulai seeding data master barang jadi...")

        items = [
            {
                "sku": "FG-CHR-001",
                "name": "Kursi Kerja Ergonomis Mesh Hitam (Hydraulic)",
                "unit": "unit",
                "standard_cost": Decimal("850000"),
                "initial_stock": Decimal("45"),
                "notes": "Kursi kantor sandaran jaring, armrest adjustable"
            },
            {
                "sku": "FG-CHR-002",
                "name": "Kursi Direktur Kulit Sintetis Reclining",
                "unit": "unit",
                "standard_cost": Decimal("1850000"),
                "initial_stock": Decimal("15"),
                "notes": "Bahan oscar premium cokelat tua dengan hidrolik heavy duty"
            },
            {
                "sku": "FG-CAB-001",
                "name": "Credenza Cabinet 2 Pintu Minimalis Woodgrain",
                "unit": "unit",
                "standard_cost": Decimal("1750000"),
                "initial_stock": Decimal("20"),
                "notes": "Plywood laminasi HPL teakwood 120x40x75cm"
            },
            {
                "sku": "FG-CAB-002",
                "name": "Mobile Drawer Pedestal 3 Laci Central Lock",
                "unit": "unit",
                "standard_cost": Decimal("650000"),
                "initial_stock": Decimal("35"),
                "notes": "Laci sorong portable dengan roda nylon & rel slow motion"
            },
            {
                "sku": "FG-LMP-001",
                "name": "Lampu Gantung Linear LED Office 120cm 36W",
                "unit": "set",
                "standard_cost": Decimal("350000"),
                "initial_stock": Decimal("60"),
                "notes": "Body aluminium hitam anodized, cahaya natural white 4000K"
            },
            {
                "sku": "FG-LMP-002",
                "name": "Downlight LED Recessed COB 12W Warm White",
                "unit": "pcs",
                "standard_cost": Decimal("115000"),
                "initial_stock": Decimal("120"),
                "notes": "Lampu plafon recessed fitting 4 inch"
            },
            {
                "sku": "FG-TBL-001",
                "name": "Meja Rapat Conference Table 8-10 Person 240x120cm",
                "unit": "unit",
                "standard_cost": Decimal("4800000"),
                "initial_stock": Decimal("8"),
                "notes": "Top table HPL marble finish include cable grommet box"
            },
            {
                "sku": "FG-ACC-001",
                "name": "Outlet Box Meja Flip-Up (2 Power + HDMI + LAN)",
                "unit": "set",
                "standard_cost": Decimal("280000"),
                "initial_stock": Decimal("50"),
                "notes": "Aluminium socket box tanam meja kerja"
            }
        ]

        created_count = 0
        updated_count = 0

        for item in items:
            fg, created = FinishedGood.objects.update_or_create(
                sku=item["sku"],
                defaults={
                    "name": item["name"],
                    "unit": item["unit"],
                    "standard_cost": item["standard_cost"],
                    "current_stock": item["initial_stock"],
                    "notes": item["notes"],
                }
            )

            # Buat record mutasi stock awal (IN) jika belum ada
            mutation, mut_created = FinishedGoodStockMutation.objects.get_or_create(
                finished_good=fg,
                reference_no=f"INIT-{fg.sku}",
                defaults={
                    "mutation_type": "IN",
                    "quantity": item["initial_stock"],
                    "balance_after": item["initial_stock"],
                    "notes": "Saldo awal persediaan barang jadi gudang"
                }
            )
            if not mut_created:
                mutation.quantity = item["initial_stock"]
                mutation.balance_after = item["initial_stock"]
                mutation.save()

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding barang jadi selesai: {created_count} baru dibuat, {updated_count} diperbarui (Total {len(items)} SKU)."
            )
        )
