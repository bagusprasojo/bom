from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import UnitMaster

def unit_list(request):
    """Daftar & Manajemen Master Satuan"""
    category_filter = request.GET.get('category', '').strip()
    search = request.GET.get('q', '').strip()

    units = UnitMaster.objects.all()

    if category_filter:
        units = units.filter(category=category_filter)

    if search:
        units = units.filter(Q(code__icontains=search) | Q(name__icontains=search) | Q(description__icontains=search))

    categories = UnitMaster.CATEGORY_CHOICES

    # Statistik per kategori
    stats = {
        'total': UnitMaster.objects.count(),
        'raw_material': UnitMaster.objects.filter(category='raw_material').count(),
        'finished_good': UnitMaster.objects.filter(category='finished_good').count(),
        'labor': UnitMaster.objects.filter(category='labor').count(),
        'overhead': UnitMaster.objects.filter(category='overhead').count(),
    }

    context = {
        'units': units,
        'categories': categories,
        'category_filter': category_filter,
        'search': search,
        'stats': stats,
    }
    return render(request, 'hpp/unit_list.html', context)


def unit_create(request):
    """Tambah Satuan Baru"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'raw_material').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not code or not name:
            messages.error(request, 'Kode dan Nama Satuan wajib diisi!')
            return redirect('unit_list')

        if UnitMaster.objects.filter(code__iexact=code, category=category).exists():
            messages.error(request, f"Satuan dengan kode '{code}' pada kategori ini sudah ada!")
            return redirect('unit_list')

        UnitMaster.objects.create(
            code=code,
            name=name,
            category=category,
            description=description,
            is_active=is_active
        )
        messages.success(request, f"Satuan '{name} ({code})' berhasil ditambahkan.")
    return redirect('unit_list')


def unit_update(request, uuid):
    """Edit Satuan"""
    unit = get_object_or_404(UnitMaster, uuid=uuid)
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', unit.category).strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not code or not name:
            messages.error(request, 'Kode dan Nama Satuan wajib diisi!')
            return redirect('unit_list')

        # Cek duplikasi
        if UnitMaster.objects.filter(code__iexact=code, category=category).exclude(id=unit.id).exists():
            messages.error(request, f"Satuan dengan kode '{code}' pada kategori ini sudah ada!")
            return redirect('unit_list')

        unit.code = code
        unit.name = name
        unit.category = category
        unit.description = description
        unit.is_active = is_active
        unit.save()

        messages.success(request, f"Satuan '{name}' berhasil diperbarui.")
    return redirect('unit_list')


def unit_delete(request, uuid):
    """Hapus Satuan"""
    unit = get_object_or_404(UnitMaster, uuid=uuid)
    if request.method == 'POST':
        name = unit.name
        unit.delete()
        messages.success(request, f"Satuan '{name}' berhasil dihapus.")
    return redirect('unit_list')
