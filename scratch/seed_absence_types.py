import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from decimal import Decimal
from hpp.models import AbsenceType, Attendance

INITIAL_TYPES = [
    {
        "code": "CT",
        "name": "Cuti Tahunan",
        "category": "LEAVE",
        "is_paid": True,
        "wage_percentage": Decimal("100.00"),
        "color": "purple",
        "requires_attachment": False,
        "notes": "Hak cuti tahunan berbayar penuh sesuai UU Ketenagakerjaan.",
    },
    {
        "code": "SKD",
        "name": "Sakit (Surat Dokter)",
        "category": "SICK",
        "is_paid": True,
        "wage_percentage": Decimal("100.00"),
        "color": "amber",
        "requires_attachment": True,
        "notes": "Ketidakhadiran karena sakit disertai bukti surat keterangan dokter.",
    },
    {
        "code": "SKT",
        "name": "Sakit (Tanpa Surat)",
        "category": "SICK",
        "is_paid": False,
        "wage_percentage": Decimal("0.00"),
        "color": "amber",
        "requires_attachment": False,
        "notes": "Sakit tanpa bukti surat keterangan dokter (tidak dibayar).",
    },
    {
        "code": "IZN",
        "name": "Izin Pribadi",
        "category": "PERMIT",
        "is_paid": False,
        "wage_percentage": Decimal("0.00"),
        "color": "blue",
        "requires_attachment": False,
        "notes": "Izin keperluan pribadi tanpa pembayaran upah.",
    },
    {
        "code": "DL",
        "name": "Dinas Luar / Tugas Lapangan",
        "category": "OFFICIAL_TRAVEL",
        "is_paid": True,
        "wage_percentage": Decimal("100.00"),
        "color": "indigo",
        "requires_attachment": False,
        "notes": "Penugasan dinas resmi ke lokasi proyek atau luar kantor.",
    },
    {
        "code": "CM",
        "name": "Cuti Khusus / Melahirkan",
        "category": "LEAVE",
        "is_paid": True,
        "wage_percentage": Decimal("100.00"),
        "color": "purple",
        "requires_attachment": True,
        "notes": "Cuti menikah, melahirkan, atau duka cita keluarga inti.",
    },
    {
        "code": "ALP",
        "name": "Alpha / Mangkir",
        "category": "ABSENT",
        "is_paid": False,
        "wage_percentage": Decimal("0.00"),
        "color": "rose",
        "requires_attachment": False,
        "notes": "Tidak hadir bekerja tanpa pemberitahuan atau izin resmi.",
    },
]

print("=== SEEDING ABSENCE TYPES ===")
created_count = 0
for data in INITIAL_TYPES:
    obj, created = AbsenceType.objects.get_or_create(
        code=data["code"],
        defaults=data
    )
    if created:
        created_count += 1
        print(f"Created: {obj}")
    else:
        print(f"Already exists: {obj}")

print(f"\nTotal created: {created_count}, Total active types: {AbsenceType.objects.count()}")

# Migrate legacy attendance records
print("\n=== MIGRATING LEGACY ATTENDANCE RECORDS ===")
mapping = {
    "IJIN": AbsenceType.objects.filter(code="IZN").first(),
    "SAKIT": AbsenceType.objects.filter(code="SKD").first(),
    "ALPHA": AbsenceType.objects.filter(code="ALP").first(),
}

updated_legacy = 0
for att in Attendance.objects.filter(absence_type__isnull=True):
    if att.status in mapping and mapping[att.status]:
        att.absence_type = mapping[att.status]
        att.save()
        updated_legacy += 1
        print(f"Updated attendance #{att.id} ({att.employee.name} - {att.date}): status {att.status} -> {att.absence_type.name}")

print(f"Total legacy attendances migrated: {updated_legacy}")
