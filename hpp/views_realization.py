from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from django.db.models import Q
from .models import (
    UnitMaster,
    Project, BOMItem, ProjectLabor, ProjectOverhead, FinishedGood,
    ProjectFinishedGood, BOMItemRealization, LaborRealization,
    FinishedGoodRealization, OverheadRealization, RawMaterial
)

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
    bom_items = project.bom_items.filter(item_type="material").select_related("material_master")
    labor_items = project.labor_items.all().select_related("labor_master")
    fg_items = project.finished_good_items.all().select_related("finished_good")
    overhead_items = project.overhead_items.all()

    master_finished_goods = FinishedGood.objects.all().order_by("name")
    master_raw_materials = RawMaterial.objects.all().prefetch_related("conversions").order_by("name")

    bom_realizations = project.bom_realizations.all().select_related("bom_item", "raw_material")
    labor_realizations = project.labor_realizations.all().select_related("project_labor")
    fg_realizations = project.finished_good_realizations.all().select_related("project_fg", "finished_good")
    overhead_realizations = project.overhead_realizations.all().select_related("project_overhead")

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
    })

def realization_bom_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        bom_item_uuid = request.POST.get("bom_item_uuid", "").strip()
        raw_material_uuid = request.POST.get("raw_material_uuid", "").strip()
        date = request.POST.get("date")
        item_name = request.POST.get("item_name", "").strip()
        unit = request.POST.get("unit", "pcs").strip()
        qty = Decimal(request.POST.get("qty") or 0)
        unit_cost = Decimal(request.POST.get("unit_cost") or 0)
        is_substitute = request.POST.get("is_substitute") == "1"
        notes = request.POST.get("notes", "").strip()

        bom_item = None
        raw_material = None

        if bom_item_uuid:
            bom_item = BOMItem.objects.filter(uuid=bom_item_uuid, project=project).first()
            if bom_item and not item_name:
                item_name = bom_item.name
                if not unit:
                    unit = bom_item.unit

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
        messages.success(request, f"Realisasi material '{item_name}' ({qty} {unit}) berhasil disimpan & stok diperbarui.")
    return redirect("project_realization_detail", uuid=project.uuid)

def realization_bom_delete(request, uuid):
    realization = get_object_or_404(BOMItemRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    realization.delete()
    messages.success(request, "Log realisasi material berhasil dibatalkan dan stok dikembalikan.")
    return redirect("project_realization_detail", uuid=project_uuid)

def realization_labor_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        labor_item_uuid = request.POST.get("labor_item_uuid", "").strip()
        date = request.POST.get("date")
        role_name = request.POST.get("role_name", "").strip()
        unit = request.POST.get("unit", "jam").strip()
        quantity = Decimal(request.POST.get("quantity") or 0)
        rate = Decimal(request.POST.get("rate") or 0)
        is_additional = request.POST.get("is_additional") == "1"
        notes = request.POST.get("notes", "").strip()

        project_labor = None
        if labor_item_uuid:
            project_labor = ProjectLabor.objects.filter(uuid=labor_item_uuid, project=project).first()
            if project_labor and not role_name:
                role_name = project_labor.role_name
                unit = project_labor.unit

        if quantity <= 0:
            messages.error(request, "Jumlah tenaga kerja harus lebih besar dari 0.")
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

def realization_labor_delete(request, uuid):
    realization = get_object_or_404(LaborRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    realization.delete()
    messages.success(request, "Log realisasi tenaga kerja berhasil dihapus.")
    return redirect("project_realization_detail", uuid=project_uuid)

def realization_fg_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        project_fg_uuid = request.POST.get("project_fg_uuid", "").strip()
        fg_uuid = request.POST.get("fg_uuid", "").strip()
        date = request.POST.get("date")
        quantity = Decimal(request.POST.get("quantity") or 0)
        unit_cost = Decimal(request.POST.get("unit_cost") or 0)
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

def realization_fg_delete(request, uuid):
    realization = get_object_or_404(FinishedGoodRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    realization.delete()
    messages.success(request, "Log realisasi barang jadi dibatalkan dan stock telah dikembalikan.")
    return redirect("project_realization_detail", uuid=project_uuid)

def realization_overhead_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        overhead_item_uuid = request.POST.get("overhead_item_uuid", "").strip()
        date = request.POST.get("date")
        expense_name = request.POST.get("expense_name", "").strip()
        cost = Decimal(request.POST.get("cost") or 0)
        is_additional = request.POST.get("is_additional") == "1"
        notes = request.POST.get("notes", "").strip()

        project_overhead = None
        if overhead_item_uuid:
            project_overhead = ProjectOverhead.objects.filter(uuid=overhead_item_uuid, project=project).first()
            if project_overhead and not expense_name:
                expense_name = project_overhead.name

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

def realization_overhead_delete(request, uuid):
    realization = get_object_or_404(OverheadRealization, uuid=uuid)
    project_uuid = realization.project.uuid
    realization.delete()
    messages.success(request, "Log realisasi overhead berhasil dihapus.")
    return redirect("project_realization_detail", uuid=project_uuid)
