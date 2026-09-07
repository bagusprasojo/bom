from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import json
from .models import (
    UnitMaster,
    Project, BOMItem, ProjectLabor, ProjectOverhead, FinishedGood,
    ProjectFinishedGood, BOMItemRealization, LaborRealization,
    FinishedGoodRealization, OverheadRealization, RawMaterial
)


def _clean_decimal(val_str, default=Decimal(0)):
    if not val_str:
        return default
    if isinstance(val_str, (int, float, Decimal)):
        return Decimal(str(val_str))
    cleaned = str(val_str).strip()
    cleaned = cleaned.replace("Rp", "").replace("rp", "").replace("RP", "").strip()
    cleaned = cleaned.replace(" ", "")
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        elif len(parts) == 2 and len(parts[1]) == 3:
            cleaned = cleaned.replace(".", "")
    try:
        return Decimal(cleaned)
    except Exception:
        return default


def project_realization_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    projects = Project.objects.all().order_by("-created_at")
    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(code__icontains=query) | Q(customer_name__icontains=query))
    if status:
        projects = projects.filter(status=status)

    return render(request, "hpp/project_realization_list.html", {
        "projects": projects,
        "query": query,
        "selected_status": status,
        "status_choices": Project.STATUS_CHOICES,
    })


def project_realization_detail(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    bom_items = project.bom_items.filter(item_type="material").select_related("material_master", "raw_material")
    labor_items = project.labor_items.all().select_related("labor_master")
    fg_items = project.finished_good_items.all().select_related("finished_good")
    overhead_items = project.overhead_items.all()

    master_finished_goods = FinishedGood.objects.all().order_by("name")
    master_raw_materials = RawMaterial.objects.all().prefetch_related("conversions").order_by("name")

    bom_realizations = project.bom_realizations.all().select_related("bom_item", "raw_material")
    labor_realizations = project.labor_realizations.all().select_related("project_labor")
    fg_realizations = project.finished_good_realizations.all().select_related("project_fg", "finished_good")
    overhead_realizations = project.overhead_realizations.all().select_related("project_overhead")

    # Serialize Master Raw Materials
    raw_materials_list = []
    for rm in master_raw_materials:
        raw_materials_list.append({
            "uuid": str(rm.uuid),
            "code": rm.code,
            "name": rm.name,
            "category": rm.category or "Umum",
            "stock_unit": rm.stock_unit,
            "current_stock": float(rm.current_stock),
            "last_purchase_price": float(rm.last_purchase_price),
            "conversions": [
                {
                    "unit_name": c.unit_name,
                    "conversion_factor": float(c.conversion_factor)
                } for c in rm.conversions.all()
            ]
        })

    # Serialize Planned BOM Items
    bom_items_list = []
    for b in bom_items:
        rm = b.raw_material
        if not rm and b.name:
            rm = RawMaterial.objects.filter(name__iexact=b.name.strip()).first()
        rm_uuid = str(rm.uuid) if rm else ""
        current_stock = float(rm.current_stock) if rm else 0
        stock_unit = rm.stock_unit if rm else b.unit
        bom_items_list.append({
            "uuid": str(b.uuid),
            "name": b.name,
            "unit": b.unit,
            "est_qty": float(b.est_qty),
            "est_unit_cost": float(b.est_unit_cost),
            "raw_material_uuid": rm_uuid,
            "current_stock": current_stock,
            "stock_unit": stock_unit,
        })

    # Serialize Planned Labor Items
    labor_items_list = []
    for l in labor_items:
        labor_items_list.append({
            "uuid": str(l.uuid),
            "role_name": l.role_name,
            "unit": l.unit,
            "est_quantity": float(l.est_quantity),
            "est_rate": float(l.est_rate),
        })

    # Serialize Master Finished Goods
    finished_goods_list = []
    for fg in master_finished_goods:
        finished_goods_list.append({
            "uuid": str(fg.uuid),
            "sku": fg.sku,
            "name": fg.name,
            "unit": fg.unit,
            "current_stock": float(fg.current_stock),
            "standard_cost": float(fg.standard_cost),
        })

    # Serialize Planned FG Items
    fg_items_list = []
    for pfg in fg_items:
        fg_items_list.append({
            "uuid": str(pfg.uuid),
            "fg_uuid": str(pfg.finished_good.uuid),
            "sku": pfg.finished_good.sku,
            "name": pfg.finished_good.name,
            "unit": pfg.finished_good.unit,
            "est_qty": float(pfg.est_qty),
            "est_unit_cost": float(pfg.est_unit_cost),
            "current_stock": float(pfg.finished_good.current_stock),
        })

    # Serialize Planned Overhead Items
    overhead_items_list = []
    for o in overhead_items:
        overhead_items_list.append({
            "uuid": str(o.uuid),
            "name": o.name,
            "est_cost": float(o.est_cost),
            "notes": o.notes or "",
        })

    unit_materials = UnitMaster.objects.filter(category="raw_material", is_active=True).order_by("name")
    unit_labors = UnitMaster.objects.filter(category="labor", is_active=True).order_by("name")

    return render(request, "hpp/project_realization_detail.html", {
        "project": project,
        "bom_items": bom_items,
        "labor_items": labor_items,
        "fg_items": fg_items,
        "overhead_items": overhead_items,
        "master_finished_goods": master_finished_goods,
        "master_raw_materials": master_raw_materials,
        "bom_realizations": bom_realizations,
        "labor_realizations": labor_realizations,
        "fg_realizations": fg_realizations,
        "overhead_realizations": overhead_realizations,
        "raw_materials_json": json.dumps(raw_materials_list),
        "bom_items_json": json.dumps(bom_items_list),
        "labor_items_json": json.dumps(labor_items_list),
        "finished_goods_json": json.dumps(finished_goods_list),
        "fg_items_json": json.dumps(fg_items_list),
        "overhead_items_json": json.dumps(overhead_items_list),
        "unit_materials": unit_materials,
        "unit_labors": unit_labors,
    })


@transaction.atomic
def realization_bom_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        bom_item_uuid = request.POST.get("bom_item_uuid", "").strip()
        raw_material_uuid = request.POST.get("raw_material_uuid", "").strip()
        date = request.POST.get("date")
        item_name = request.POST.get("item_name", "").strip()
        unit = request.POST.get("unit", "pcs").strip()
        qty = _clean_decimal(request.POST.get("qty"), Decimal(0))
        unit_cost = _clean_decimal(request.POST.get("unit_cost"), Decimal(0))
        is_substitute = request.POST.get("is_substitute") == "1"
        notes = request.POST.get("notes", "").strip()

        bom_item = None
        raw_material = None

        if bom_item_uuid:
            bom_item = BOMItem.objects.filter(uuid=bom_item_uuid, project=project).first()
            if bom_item:
                if not item_name:
                    item_name = bom_item.name
                if not unit:
                    unit = bom_item.unit
                if bom_item.raw_material and not raw_material_uuid:
                    raw_material = bom_item.raw_material

        if raw_material_uuid:
            raw_material = RawMaterial.objects.filter(uuid=raw_material_uuid).first()
            if raw_material:
                if not item_name:
                    item_name = raw_material.name
                if not unit:
                    unit = raw_material.stock_unit
                if unit_cost == 0:
                    unit_cost = raw_material.last_purchase_price

        if not item_name:
            messages.error(request, "Nama material harus diisi.")
            return redirect("project_realization_detail", uuid=project.uuid)

        if qty <= 0:
            messages.error(request, "Quantity realisasi material harus lebih besar dari 0.")
            return redirect("project_realization_detail", uuid=project.uuid)

        BOMItemRealization.objects.create(
            project=project,
            bom_item=bom_item,
            raw_material=raw_material,
            date=date,
            item_name=item_name,
            unit=unit,
            qty=qty,
            unit_cost=unit_cost,
            is_substitute=is_substitute,
            notes=notes,
        )
        messages.success(request, f"Realisasi material '{item_name}' ({qty} {unit}) berhasil disimpan & mutasi stok dicatat.")
    return redirect("project_realization_detail", uuid=project.uuid)


@transaction.atomic
def realization_bom_delete(request, uuid):
    realization = get_object_or_404(BOMItemRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    item_name = realization.item_name
    realization.delete()
    messages.success(request, f"Log realisasi material '{item_name}' berhasil dibatalkan dan stok dikembalikan.")
    return redirect("project_realization_detail", uuid=project_uuid)


@transaction.atomic
def realization_labor_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        labor_item_uuid = request.POST.get("labor_item_uuid", "").strip()
        date = request.POST.get("date")
        role_name = request.POST.get("role_name", "").strip()
        unit = request.POST.get("unit", "jam").strip()
        quantity = _clean_decimal(request.POST.get("quantity"), Decimal(0))
        rate = _clean_decimal(request.POST.get("rate"), Decimal(0))
        is_additional = request.POST.get("is_additional") == "1"
        notes = request.POST.get("notes", "").strip()

        project_labor = None
        if labor_item_uuid:
            project_labor = ProjectLabor.objects.filter(uuid=labor_item_uuid, project=project).first()
            if project_labor:
                if not role_name:
                    role_name = project_labor.role_name
                if not unit:
                    unit = project_labor.unit

        if not role_name:
            messages.error(request, "Nama/Peran tenaga kerja harus diisi.")
            return redirect("project_realization_detail", uuid=project.uuid)

        if quantity <= 0:
            messages.error(request, "Jumlah/durasi tenaga kerja harus lebih besar dari 0.")
            return redirect("project_realization_detail", uuid=project.uuid)

        LaborRealization.objects.create(
            project=project,
            project_labor=project_labor,
            date=date,
            role_name=role_name,
            unit=unit,
            quantity=quantity,
            rate=rate,
            is_additional=is_additional,
            notes=notes,
        )
        messages.success(request, f"Realisasi tenaga kerja '{role_name}' ({quantity} {unit}) berhasil disimpan.")
    return redirect("project_realization_detail", uuid=project.uuid)


@transaction.atomic
def realization_labor_delete(request, uuid):
    realization = get_object_or_404(LaborRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    role_name = realization.role_name
    realization.delete()
    messages.success(request, f"Log realisasi tenaga kerja '{role_name}' berhasil dihapus.")
    return redirect("project_realization_detail", uuid=project_uuid)


@transaction.atomic
def realization_fg_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        project_fg_uuid = request.POST.get("project_fg_uuid", "").strip()
        fg_uuid = request.POST.get("fg_uuid", "").strip()
        date = request.POST.get("date")
        quantity = _clean_decimal(request.POST.get("quantity"), Decimal(0))
        unit_cost = _clean_decimal(request.POST.get("unit_cost"), Decimal(0))
        notes = request.POST.get("notes", "").strip()

        project_fg = None
        finished_good = None

        if project_fg_uuid:
            project_fg = ProjectFinishedGood.objects.filter(uuid=project_fg_uuid, project=project).first()
            if project_fg:
                finished_good = project_fg.finished_good
                if unit_cost == 0:
                    unit_cost = project_fg.est_unit_cost or finished_good.standard_cost
        elif fg_uuid:
            finished_good = FinishedGood.objects.filter(uuid=fg_uuid).first()
            if finished_good and unit_cost == 0:
                unit_cost = finished_good.standard_cost

        if not finished_good:
            messages.error(request, "Barang Jadi tidak valid.")
            return redirect("project_realization_detail", uuid=project.uuid)

        if quantity <= 0:
            messages.error(request, "Jumlah pemakaian barang jadi harus lebih besar dari 0.")
            return redirect("project_realization_detail", uuid=project.uuid)

        if finished_good.current_stock < quantity:
            messages.error(request, f"Stock {finished_good.name} tidak cukup (Tersedia: {finished_good.current_stock} {finished_good.unit}).")
            return redirect("project_realization_detail", uuid=project.uuid)

        FinishedGoodRealization.objects.create(
            project=project,
            project_fg=project_fg,
            finished_good=finished_good,
            date=date,
            quantity=quantity,
            unit_cost=unit_cost,
            notes=notes,
        )
        messages.success(request, f"Realisasi {finished_good.name} ({quantity} {finished_good.unit}) berhasil dicatat dan memotong stock.")
    return redirect("project_realization_detail", uuid=project.uuid)


@transaction.atomic
def realization_fg_delete(request, uuid):
    realization = get_object_or_404(FinishedGoodRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    fg_name = realization.finished_good.name
    realization.delete()
    messages.success(request, f"Log realisasi barang jadi '{fg_name}' dibatalkan dan stock telah dikembalikan.")
    return redirect("project_realization_detail", uuid=project_uuid)


@transaction.atomic
def realization_overhead_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        overhead_item_uuid = request.POST.get("overhead_item_uuid", "").strip()
        date = request.POST.get("date")
        expense_name = request.POST.get("expense_name", "").strip()
        cost = _clean_decimal(request.POST.get("cost"), Decimal(0))
        is_additional = request.POST.get("is_additional") == "1"
        notes = request.POST.get("notes", "").strip()

        project_overhead = None
        if overhead_item_uuid:
            project_overhead = ProjectOverhead.objects.filter(uuid=overhead_item_uuid, project=project).first()
            if project_overhead and not expense_name:
                expense_name = project_overhead.name

        if not expense_name:
            messages.error(request, "Nama pos pengeluaran overhead harus diisi.")
            return redirect("project_realization_detail", uuid=project.uuid)

        if cost <= 0:
            messages.error(request, "Biaya overhead harus lebih besar dari 0.")
            return redirect("project_realization_detail", uuid=project.uuid)

        OverheadRealization.objects.create(
            project=project,
            project_overhead=project_overhead,
            date=date,
            expense_name=expense_name,
            cost=cost,
            is_additional=is_additional,
            notes=notes,
        )
        messages.success(request, f"Realisasi overhead '{expense_name}' berhasil disimpan.")
    return redirect("project_realization_detail", uuid=project.uuid)


@transaction.atomic
def realization_overhead_delete(request, uuid):
    realization = get_object_or_404(OverheadRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    expense_name = realization.expense_name
    realization.delete()
    messages.success(request, f"Log realisasi overhead '{expense_name}' berhasil dihapus.")
    return redirect("project_realization_detail", uuid=project_uuid)

