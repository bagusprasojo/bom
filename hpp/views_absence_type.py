from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from .models import AbsenceType, Attendance
from .views_auth import menu_permission_required


@menu_permission_required("MENU_ABSENCE_TYPE")
def absence_type_list(request):
    """
    Daftar Master Jenis Tidak Masuk Karyawan
    (Cuti, Izin, Sakit, Dinas Luar, Alpha, dll.)
    Dilengkapi KPI ringkasan, pencarian, dan modal Tambah/Edit.
    """
    query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()
    status_filter = request.GET.get("status", "").strip()

    absence_types = AbsenceType.objects.annotate(
        usage_count=Count("attendances")
    ).order_by("category", "code")

    if query:
        absence_types = absence_types.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(notes__icontains=query)
        )
    if category_filter:
        absence_types = absence_types.filter(category=category_filter)
    if status_filter == "active":
        absence_types = absence_types.filter(is_active=True)
    elif status_filter == "inactive":
        absence_types = absence_types.filter(is_active=False)

    # KPI Summary
    all_types = AbsenceType.objects.all()
    total_types = all_types.count()
    total_paid = all_types.filter(is_paid=True).count()
    total_unpaid = all_types.filter(is_paid=False).count()
    total_active = all_types.filter(is_active=True).count()

    return render(request, "hpp/absence_type_list.html", {
        "absence_types": absence_types,
        "query": query,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "category_choices": AbsenceType.CATEGORY_CHOICES,
        "color_choices": AbsenceType.COLOR_CHOICES,
        "total_types": total_types,
        "total_paid": total_paid,
        "total_unpaid": total_unpaid,
        "total_active": total_active,
    })


def absence_type_create(request):
    """
    Tambah Master Jenis Tidak Masuk Baru
    """
    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "PERMIT")
        is_paid = request.POST.get("is_paid") == "on" or request.POST.get("is_paid") == "true"
        wage_pct_raw = request.POST.get("wage_percentage", "0").strip()
        color = request.POST.get("color", "blue")
        requires_attachment = request.POST.get("requires_attachment") == "on" or request.POST.get("requires_attachment") == "true"
        notes = request.POST.get("notes", "").strip()
        is_active = request.POST.get("is_active") == "on" or request.POST.get("is_active") == "true" or "is_active" not in request.POST

        if not code or not name:
            messages.error(request, "Kode dan Nama Jenis Tidak Masuk wajib diisi!")
            return redirect("absence_type_list")

        if AbsenceType.objects.filter(code=code).exists():
            messages.error(request, f"Kode Jenis '{code}' sudah digunakan! Silakan gunakan kode unik lain.")
            return redirect("absence_type_list")

        try:
            wage_percentage = Decimal(wage_pct_raw) if wage_pct_raw else Decimal("0.00")
            if wage_percentage < 0 or wage_percentage > 100:
                messages.error(request, "Persentase upah harian harus berada di antara 0% dan 100%!")
                return redirect("absence_type_list")
        except Exception:
            wage_percentage = Decimal("0.00")

        # Sinkronisasi is_paid dengan wage_percentage
        if not is_paid and wage_percentage > 0:
            is_paid = True
        elif is_paid and wage_percentage == 0:
            wage_percentage = Decimal("100.00")

        obj = AbsenceType.objects.create(
            code=code,
            name=name,
            category=category,
            is_paid=is_paid,
            wage_percentage=wage_percentage,
            color=color,
            requires_attachment=requires_attachment,
            notes=notes,
            is_active=is_active,
        )
        messages.success(request, f"Jenis tidak masuk '{obj.name}' [{obj.code}] berhasil ditambahkan.")
        return redirect("absence_type_list")

    return redirect("absence_type_list")


def absence_type_update(request, uuid):
    """
    Perbarui Master Jenis Tidak Masuk
    """
    obj = get_object_or_404(AbsenceType, uuid=uuid)

    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", obj.category)
        is_paid = request.POST.get("is_paid") == "on" or request.POST.get("is_paid") == "true"
        wage_pct_raw = request.POST.get("wage_percentage", "0").strip()
        color = request.POST.get("color", obj.color)
        requires_attachment = request.POST.get("requires_attachment") == "on" or request.POST.get("requires_attachment") == "true"
        notes = request.POST.get("notes", "").strip()
        is_active = request.POST.get("is_active") == "on" or request.POST.get("is_active") == "true"

        if not code or not name:
            messages.error(request, "Kode dan Nama Jenis Tidak Masuk wajib diisi!")
            return redirect("absence_type_list")

        # Cek kode unik jika diubah
        if code != obj.code and AbsenceType.objects.filter(code=code).exclude(uuid=uuid).exists():
            messages.error(request, f"Kode Jenis '{code}' sudah digunakan oleh data lain!")
            return redirect("absence_type_list")

        try:
            wage_percentage = Decimal(wage_pct_raw) if wage_pct_raw else Decimal("0.00")
            if wage_percentage < 0 or wage_percentage > 100:
                messages.error(request, "Persentase upah harian harus berada di antara 0% dan 100%!")
                return redirect("absence_type_list")
        except Exception:
            wage_percentage = Decimal("0.00")

        if not is_paid and wage_percentage > 0:
            is_paid = True
        elif is_paid and wage_percentage == 0:
            wage_percentage = Decimal("100.00")

        obj.code = code
        obj.name = name
        obj.category = category
        obj.is_paid = is_paid
        obj.wage_percentage = wage_percentage
        obj.color = color
        obj.requires_attachment = requires_attachment
        obj.notes = notes
        obj.is_active = is_active
        obj.save()

        messages.success(request, f"Jenis tidak masuk '{obj.name}' berhasil diperbarui.")
        return redirect("absence_type_list")

    return redirect("absence_type_list")


def absence_type_delete(request, uuid):
    """
    Hapus Master Jenis Tidak Masuk
    Dilindungi pencegahan penghapusan jika sudah digunakan pada riwayat absensi.
    """
    obj = get_object_or_404(AbsenceType, uuid=uuid)

    if request.method == "POST":
        usage_count = obj.attendances.count()
        if usage_count > 0:
            messages.error(
                request,
                f"Tidak dapat menghapus '{obj.name}' [{obj.code}] karena telah digunakan oleh "
                f"{usage_count} data absensi karyawan! Anda dapat menonaktifkannya (Uncheck Status Aktif) "
                f"agar tidak muncul dalam pilihan absensi baru."
            )
            return redirect("absence_type_list")

        type_name = obj.name
        type_code = obj.code
        obj.delete()
        messages.success(request, f"Jenis tidak masuk '{type_name}' [{type_code}] berhasil dihapus.")
        return redirect("absence_type_list")

    return redirect("absence_type_list")
