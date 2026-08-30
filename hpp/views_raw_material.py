from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
from .models import UnitMaster, RawMaterial, RawMaterialUnitConversion, RawMaterialStockMutation

def raw_material_list(request):
    """
    Laporan Persediaan Bahan Baku (Valuasi Berdasarkan Harga Beli Terakhir)
    """
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    materials = RawMaterial.objects.all().prefetch_related("conversions").order_by("name")
    if query:
        materials = materials.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(category__icontains=query) |
            Q(notes__icontains=query)
        )
    if category:
        materials = materials.filter(category=category)

    total_inventory_value = sum(m.total_inventory_value for m in materials)
    total_sku_count = materials.count()
    low_stock_count = sum(1 for m in materials if m.current_stock <= m.minimum_stock)

    categories = RawMaterial.objects.values_list("category", flat=True).distinct()

    unit_materials = UnitMaster.objects.filter(category="raw_material", is_active=True).order_by("name")

    return render(request, "hpp/raw_material_list.html", {
        "materials": materials,
        "query": query,
        "selected_category": category,
        "categories": categories,
        "total_inventory_value": total_inventory_value,
        "total_sku_count": total_sku_count,
        "low_stock_count": low_stock_count,
        "unit_materials": unit_materials,
    })

def raw_material_create(request):
    """
    Tambah Master Bahan Baku Baru beserta Multi-Satuan
    """
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "Umum").strip()
        stock_unit = request.POST.get("stock_unit", "pcs").strip()
        initial_stock = Decimal(request.POST.get("initial_stock") or 0)
        last_purchase_price = Decimal(request.POST.get("last_purchase_price") or 0)
        minimum_stock = Decimal(request.POST.get("minimum_stock") or 0)
        notes = request.POST.get("notes", "").strip()

        if not code:
            last = RawMaterial.objects.order_by("-id").first()
            next_id = (last.id + 1) if last else 1
            code = f"MAT-{next_id:04d}"

        if RawMaterial.objects.filter(code=code).exists():
            messages.error(request, f"Kode {code} sudah terdaftar.")
            return redirect("raw_material_list")

        rm = RawMaterial.objects.create(
            code=code,
            name=name,
            category=category,
            stock_unit=stock_unit,
            current_stock=initial_stock,
            last_purchase_price=last_purchase_price,
            minimum_stock=minimum_stock,
            notes=notes,
        )

        if initial_stock > 0:
            RawMaterialStockMutation.objects.create(
                raw_material=rm,
                mutation_type="IN",
                input_qty=initial_stock,
                input_unit=stock_unit,
                stock_qty=initial_stock,
                unit_price=last_purchase_price,
                total_price=initial_stock * last_purchase_price,
                balance_after=initial_stock,
                reference_no=f"INIT-{rm.code}",
                notes="Saldo stock awal"
            )

        messages.success(request, f"Bahan baku '{name}' berhasil didaftarkan.")
        return redirect("raw_material_list")

    return render(request, "hpp/raw_material_form.html")

def raw_material_update(request, uuid):
    rm = get_object_or_404(RawMaterial, uuid=uuid)
    if request.method == "POST":
        rm.code = request.POST.get("code", rm.code).strip()
        rm.name = request.POST.get("name", rm.name).strip()
        rm.category = request.POST.get("category", rm.category).strip()
        rm.stock_unit = request.POST.get("stock_unit", rm.stock_unit).strip()
        rm.last_purchase_price = Decimal(request.POST.get("last_purchase_price") or 0)
        rm.minimum_stock = Decimal(request.POST.get("minimum_stock") or 0)
        rm.notes = request.POST.get("notes", "").strip()
        rm.save()
        messages.success(request, f"Data bahan baku '{rm.name}' berhasil diperbarui.")
    return redirect("raw_material_list")

def raw_material_delete(request, uuid):
    rm = get_object_or_404(RawMaterial, uuid=uuid)
    if rm.mutations.exists():
        messages.error(request, f"Bahan baku '{rm.name}' tidak dapat dihapus karena sudah memiliki riwayat mutasi.")
    else:
        name = rm.name
        rm.delete()
        messages.success(request, f"Bahan baku '{name}' berhasil dihapus.")
    return redirect("raw_material_list")

def raw_material_conversion_add(request, material_uuid):
    rm = get_object_or_404(RawMaterial, uuid=material_uuid)
    if request.method == "POST":
        unit_name = request.POST.get("unit_name", "").strip()
        conversion_factor = Decimal(request.POST.get("conversion_factor") or 1)
        notes = request.POST.get("notes", "").strip()

        if conversion_factor <= 0:
            messages.error(request, "Faktor konversi harus lebih besar dari 0.")
            return redirect("raw_material_list")

        RawMaterialUnitConversion.objects.update_or_create(
            raw_material=rm,
            unit_name=unit_name,
            defaults={
                "conversion_factor": conversion_factor,
                "notes": notes
            }
        )
        messages.success(request, f"Konversi 1 {unit_name} = {conversion_factor} {rm.stock_unit} berhasil disimpan.")
    return redirect("raw_material_list")

def raw_material_conversion_delete(request, uuid):
    conv = get_object_or_404(RawMaterialUnitConversion, uuid=uuid)
    conv.delete()
    messages.success(request, "Konversi satuan berhasil dihapus.")
    return redirect("raw_material_list")

def raw_material_stock_mutation_list(request):
    mat_uuid = request.GET.get("mat", "").strip()
    mutation_type = request.GET.get("type", "").strip()
    query = request.GET.get("q", "").strip()

    mutations = RawMaterialStockMutation.objects.all().select_related("raw_material", "project")

    if mat_uuid:
        mutations = mutations.filter(raw_material__uuid=mat_uuid)
    if mutation_type:
        mutations = mutations.filter(mutation_type=mutation_type)
    if query:
        mutations = mutations.filter(
            Q(reference_no__icontains=query) |
            Q(notes__icontains=query) |
            Q(raw_material__name__icontains=query) |
            Q(raw_material__code__icontains=query)
        )

    materials = RawMaterial.objects.all().order_by("name")

    return render(request, "hpp/raw_material_mutation_list.html", {
        "mutations": mutations,
        "materials": materials,
        "selected_mat": mat_uuid,
        "selected_type": mutation_type,
        "query": query,
    })

def raw_material_mutation_create(request):
    """
    Input Mutasi Manual Masuk (Pembelian Supplier) atau Keluar (Rusak / Pemakaian Non-Project)
    """
    if request.method == "POST":
        mat_uuid = request.POST.get("material_uuid")
        mutation_type = request.POST.get("mutation_type", "IN")
        input_qty = Decimal(request.POST.get("input_qty") or 0)
        input_unit = request.POST.get("input_unit", "").strip()
        unit_price = Decimal(request.POST.get("unit_price") or 0)
        reference_no = request.POST.get("reference_no", "").strip()
        notes = request.POST.get("notes", "").strip()

        rm = get_object_or_404(RawMaterial, uuid=mat_uuid)

        if input_qty <= 0:
            messages.error(request, "Jumlah mutasi harus lebih besar dari 0.")
            return redirect("raw_material_stock_mutation_list")

        # Cek faktor konversi jika input_unit berbeda dari stock_unit
        factor = Decimal(1)
        if input_unit and input_unit.lower() != rm.stock_unit.lower():
            conv = rm.conversions.filter(unit_name__iexact=input_unit).first()
            if conv:
                factor = conv.conversion_factor
            else:
                input_unit = rm.stock_unit
        else:
            input_unit = rm.stock_unit

        base_qty = input_qty * factor
        total_price = input_qty * unit_price

        if mutation_type == "IN":
            rm.current_stock += base_qty
            if unit_price > 0:
                # Update harga beli terakhir per stock_unit
                rm.last_purchase_price = unit_price / factor
            prefix = "[MASUK/BELI]"
        else:
            if rm.current_stock < base_qty:
                messages.error(request, f"Stok {rm.name} tidak mencukupi (Tersedia: {rm.current_stock} {rm.stock_unit}).")
                return redirect("raw_material_stock_mutation_list")
            rm.current_stock -= base_qty
            prefix = "[RUSAK/OUT]"

        rm.save()

        full_notes = f"{prefix} {notes}".strip()
        RawMaterialStockMutation.objects.create(
            raw_material=rm,
            mutation_type=mutation_type,
            input_qty=input_qty,
            input_unit=input_unit,
            stock_qty=base_qty,
            unit_price=unit_price,
            total_price=total_price,
            balance_after=rm.current_stock,
            reference_no=reference_no or f"MUT-{rm.code}",
            notes=full_notes
        )
        messages.success(request, f"Mutasi bahan baku {rm.name} ({mutation_type} {input_qty} {input_unit}) berhasil dicatat.")
    return redirect("raw_material_stock_mutation_list")

def raw_material_stock_card(request, uuid):
    """
    Kartu Stok Bahan Baku Tunggal
    """
    rm = get_object_or_404(RawMaterial, uuid=uuid)
    mutations = rm.mutations.all().select_related("project")

    total_in = sum(m.stock_qty for m in mutations if m.mutation_type == "IN")
    total_out = sum(m.stock_qty for m in mutations if m.mutation_type == "OUT")

    return render(request, "hpp/raw_material_stock_card.html", {
        "material": rm,
        "mutations": mutations,
        "total_in": total_in,
        "total_out": total_out,
    })

def raw_material_stock_card_index(request):
    """
    Kartu Stok Bahan Baku Standalone (Filter Pilih Item)
    """
    materials = RawMaterial.objects.all().order_by("name")
    selected_uuid = request.GET.get("mat", "").strip()

    if selected_uuid:
        selected_mat = RawMaterial.objects.filter(uuid=selected_uuid).first()
    else:
        selected_mat = materials.first()

    mutations = []
    total_in = 0
    total_out = 0

    if selected_mat:
        mutations = selected_mat.mutations.all().select_related("project")
        total_in = sum(m.stock_qty for m in mutations if m.mutation_type == "IN")
        total_out = sum(m.stock_qty for m in mutations if m.mutation_type == "OUT")

    return render(request, "hpp/raw_material_stock_card_index.html", {
        "materials": materials,
        "selected_mat": selected_mat,
        "mutations": mutations,
        "total_in": total_in,
        "total_out": total_out,
    })
