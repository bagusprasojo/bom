from .utils import generate_project_code, get_ordered_bom
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal
from datetime import datetime
import json
import openpyxl
from openpyxl.styles import Font, PatternFill

from .models import (
    UnitMaster,
    Customer,
    Employee, Attendance, EmployeeWorkLog,
    Project, BOMItem, ProjectLabor, ProjectOverhead,
    MaterialMaster, LaborMaster, FinishedGood,
    ProjectFinishedGood, FinishedGoodStockMutation,
    RawMaterial
)


# =========================================================================
# PROJECT VIEWS
# =========================================================================
def project_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    start_date_from = request.GET.get("start_date_from", "").strip()
    start_date_to = request.GET.get("start_date_to", "").strip()

    projects = Project.objects.all().order_by("-created_at")
    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(code__icontains=query) | Q(customer_name__icontains=query))
    if status:
        projects = projects.filter(status=status)
    if start_date_from:
        projects = projects.filter(start_date__gte=start_date_from)
    if start_date_to:
        projects = projects.filter(start_date__lte=start_date_to)

    return render(request, "hpp/project_list.html", {
        "projects": projects,
        "query": query,
        "selected_status": status,
        "start_date_from": start_date_from,
        "start_date_to": start_date_to,
        "status_choices": Project.STATUS_CHOICES,
    })


@transaction.atomic
def project_create(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip() or generate_project_code()
        name = request.POST.get("name", "").strip()
        customer_uuid = request.POST.get("customer_uuid", "").strip()
        customer = Customer.objects.filter(uuid=customer_uuid).first() if customer_uuid else None
        manual_customer_name = request.POST.get("customer_name", "").strip()
        customer_name = str(customer) if customer else manual_customer_name

        raw_contract = request.POST.get("contract_value", "0").strip()
        clean_contract = raw_contract.replace("Rp", "").replace("rp", "").replace(" ", "")
        if "," in clean_contract and "." in clean_contract:
            clean_contract = clean_contract.replace(".", "").replace(",", ".")
        elif "." in clean_contract and "," not in clean_contract:
            parts = clean_contract.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                clean_contract = clean_contract.replace(".", "")
        elif "," in clean_contract:
            clean_contract = clean_contract.replace(",", ".")

        try:
            contract_value = Decimal(clean_contract or 0)
            if contract_value < 0:
                contract_value = Decimal(0)
        except Exception:
            contract_value = Decimal(0)

        try:
            progress_percentage = int(request.POST.get("progress_percentage") or 0)
            progress_percentage = max(0, min(100, progress_percentage))
        except (ValueError, TypeError):
            progress_percentage = 0

        status = request.POST.get("status", "draft")
        start_date = request.POST.get("start_date") or None
        target_date = request.POST.get("target_date") or None
        notes = request.POST.get("notes", "").strip()

        # Validasi: Nama project wajib diisi
        if not name:
            messages.error(request, "Nama project wajib diisi.")
            customers = Customer.objects.all().order_by("name")
            customers_json = json.dumps([
                {
                    "uuid": str(c.uuid),
                    "code": c.code,
                    "name": c.name,
                    "company_name": c.company_name or "",
                    "label": str(c),
                }
                for c in customers
            ])
            return render(request, "hpp/project_form.html", {
                "status_choices": Project.STATUS_CHOICES,
                "auto_code": code or generate_project_code(),
                "customers": customers,
                "customers_json": customers_json,
                "form_data": request.POST,
            })

        # Validasi: Urutan tanggal
        if start_date and target_date:
            try:
                s_d = datetime.strptime(start_date, "%Y-%m-%d").date()
                t_d = datetime.strptime(target_date, "%Y-%m-%d").date()
                if t_d < s_d:
                    messages.error(request, "Target tanggal selesai tidak boleh lebih awal dari tanggal mulai pengerjaan.")
                    customers = Customer.objects.all().order_by("name")
                    customers_json = json.dumps([
                        {
                            "uuid": str(c.uuid),
                            "code": c.code,
                            "name": c.name,
                            "company_name": c.company_name or "",
                            "label": str(c),
                        }
                        for c in customers
                    ])
                    return render(request, "hpp/project_form.html", {
                        "status_choices": Project.STATUS_CHOICES,
                        "auto_code": code or generate_project_code(),
                        "customers": customers,
                        "customers_json": customers_json,
                        "form_data": request.POST,
                    })
            except ValueError:
                pass

        if Project.objects.filter(code=code).exists():
            code = generate_project_code()

        project = Project.objects.create(
            code=code,
            name=name,
            customer=customer,
            customer_name=customer_name,
            contract_value=contract_value,
            progress_percentage=progress_percentage,
            status=status,
            start_date=start_date,
            target_date=target_date,
            notes=notes,
        )
        project.release_stock_if_completed()
        messages.success(request, f"Project '{project.name}' ({project.code}) berhasil dibuat! Silakan lengkapi Bill of Materials (BOM).")
        return redirect("project_detail", uuid=project.uuid)

    auto_code = generate_project_code()
    customers = Customer.objects.all().order_by("name")
    customers_json = json.dumps([
        {
            "uuid": str(c.uuid),
            "code": c.code,
            "name": c.name,
            "company_name": c.company_name or "",
            "label": str(c),
        }
        for c in customers
    ])
    return render(request, "hpp/project_form.html", {
        "status_choices": Project.STATUS_CHOICES,
        "auto_code": auto_code,
        "customers": customers,
        "customers_json": customers_json,
    })


def _clean_decimal(val_str, default=Decimal(0)):
    if val_str is None:
        return default
    if isinstance(val_str, (int, float, Decimal)):
        return Decimal(str(val_str))
    cleaned = str(val_str).replace("Rp", "").replace("rp", "").replace(" ", "").strip()
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "." in cleaned and "," not in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            cleaned = cleaned.replace(".", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        res = Decimal(cleaned or 0)
        return res if res >= 0 else Decimal(0)
    except Exception:
        return default


def project_detail(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    materials = get_ordered_bom(project)
    labors = project.labor_items.all().select_related("labor_master")
    overheads = project.overhead_items.all()
    finished_goods = project.finished_good_items.all().select_related("finished_good")
    
    master_materials = MaterialMaster.objects.all().order_by("name")
    raw_materials = RawMaterial.objects.all().order_by("name")
    master_labors = LaborMaster.objects.all().order_by("role_name")
    master_finished_goods = FinishedGood.objects.all().order_by("name")

    unit_materials = UnitMaster.objects.filter(category="raw_material", is_active=True).order_by("name")
    unit_labors = UnitMaster.objects.filter(category="labor", is_active=True).order_by("name")
    unit_fgs = UnitMaster.objects.filter(category="finished_good", is_active=True).order_by("name")
    unit_overheads = UnitMaster.objects.filter(category="overhead", is_active=True).order_by("name")

    raw_materials_json = json.dumps([
        {
            "uuid": str(rm.uuid),
            "code": rm.code,
            "name": rm.name,
            "category": rm.category or "Umum",
            "stock_unit": rm.stock_unit,
            "current_stock": float(rm.current_stock),
            "last_purchase_price": float(rm.last_purchase_price),
            "label": f"[{rm.code}] {rm.name} (Stok: {rm.current_stock:g} {rm.stock_unit} | Rp {rm.last_purchase_price:,.0f})",
        }
        for rm in raw_materials
    ])

    master_labors_json = json.dumps([
        {
            "id": ml.id,
            "uuid": str(ml.uuid),
            "role_name": ml.role_name,
            "unit": ml.unit,
            "standard_rate": float(ml.standard_rate),
            "label": f"{ml.role_name} (Rp {ml.standard_rate:,.0f} / {ml.unit})",
        }
        for ml in master_labors
    ])

    master_finished_goods_json = json.dumps([
        {
            "uuid": str(fg.uuid),
            "sku": fg.sku,
            "name": fg.name,
            "category": fg.category or "Umum",
            "unit": fg.unit,
            "current_stock": float(fg.current_stock),
            "standard_cost": float(fg.standard_cost),
            "label": f"[{fg.sku}] {fg.name} (Stok: {fg.current_stock:g} {fg.unit} | Rp {fg.standard_cost:,.0f})",
        }
        for fg in master_finished_goods
    ])

    return render(request, "hpp/project_detail.html", {
        "project": project,
        "materials": materials,
        "labors": labors,
        "overheads": overheads,
        "finished_goods": finished_goods,
        "master_materials": master_materials,
        "raw_materials": raw_materials,
        "raw_materials_json": raw_materials_json,
        "master_labors": master_labors,
        "master_labors_json": master_labors_json,
        "master_finished_goods": master_finished_goods,
        "master_finished_goods_json": master_finished_goods_json,
        "unit_materials": unit_materials,
        "unit_labors": unit_labors,
        "unit_fgs": unit_fgs,
        "unit_overheads": unit_overheads,
        "status_choices": Project.STATUS_CHOICES,
    })


def project_update(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    if request.method == "POST":
        project.code = request.POST.get("code", project.code)
        project.name = request.POST.get("name", project.name)
        customer_uuid = request.POST.get("customer_uuid", "").strip()
        if customer_uuid:
            customer = Customer.objects.filter(uuid=customer_uuid).first()
            if customer:
                project.customer = customer
                project.customer_name = str(customer)
        elif "customer_name" in request.POST:
            project.customer_name = request.POST.get("customer_name", "")

        raw_contract = request.POST.get("contract_value", str(project.contract_value)).strip()
        clean_contract = raw_contract.replace("Rp", "").replace("rp", "").replace(" ", "")
        if "," in clean_contract and "." in clean_contract:
            clean_contract = clean_contract.replace(".", "").replace(",", ".")
        elif "." in clean_contract and "," not in clean_contract:
            parts = clean_contract.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                clean_contract = clean_contract.replace(".", "")
        elif "," in clean_contract:
            clean_contract = clean_contract.replace(",", ".")
        try:
            project.contract_value = Decimal(clean_contract or 0)
        except Exception:
            pass

        try:
            progress = int(request.POST.get("progress_percentage") or project.progress_percentage)
            project.progress_percentage = max(0, min(100, progress))
        except (ValueError, TypeError):
            pass

        project.status = request.POST.get("status", project.status)
        project.start_date = request.POST.get("start_date") or None
        project.target_date = request.POST.get("target_date") or None
        if "notes" in request.POST:
            project.notes = request.POST.get("notes", "").strip()
        project.save()
        
        # Cek trigger potong stock jika project selesai
        project.release_stock_if_completed()
        messages.success(request, f"Project '{project.name}' berhasil diperbarui.")
    return redirect("project_detail", uuid=project.uuid)


# =========================================================================
# BOM CRUD
# =========================================================================
def bom_item_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        item_type = request.POST.get("item_type", "material")
        raw_material_uuid = request.POST.get("raw_material_uuid", "").strip()
        raw_material = RawMaterial.objects.filter(uuid=raw_material_uuid).first() if raw_material_uuid else None
        if raw_material and not name:
            name = raw_material.name

        unit = request.POST.get("unit", "").strip()
        if not unit and raw_material:
            unit = raw_material.stock_unit
        if not unit:
            unit = "pcs"

        raw_est_qty = request.POST.get("est_qty", "1").strip().replace(",", ".")
        try:
            est_qty = Decimal(raw_est_qty or 1)
            if est_qty < 0:
                est_qty = Decimal(0)
        except Exception:
            est_qty = Decimal(1)

        raw_est_cost = request.POST.get("est_unit_cost", "0").strip()
        clean_cost = raw_est_cost.replace("Rp", "").replace("rp", "").replace(" ", "")
        if "," in clean_cost and "." in clean_cost:
            clean_cost = clean_cost.replace(".", "").replace(",", ".")
        elif "." in clean_cost and "," not in clean_cost:
            parts = clean_cost.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                clean_cost = clean_cost.replace(".", "")
        elif "," in clean_cost:
            clean_cost = clean_cost.replace(",", ".")
        try:
            est_unit_cost = Decimal(clean_cost or 0)
            if est_unit_cost < 0:
                est_unit_cost = Decimal(0)
        except Exception:
            est_unit_cost = Decimal(0)

        if est_unit_cost == 0 and raw_material:
            est_unit_cost = raw_material.last_purchase_price

        parent_uuid = request.POST.get("parent_uuid") or None
        parent = BOMItem.objects.filter(uuid=parent_uuid, project=project).first() if parent_uuid else None
        notes = request.POST.get("notes", "").strip()

        if not name:
            messages.error(request, "Nama item BOM wajib diisi.")
            return redirect("project_detail", uuid=project.uuid)

        BOMItem.objects.create(
            project=project,
            parent=parent,
            raw_material=raw_material,
            name=name,
            item_type=item_type,
            unit=unit,
            est_qty=est_qty,
            est_unit_cost=est_unit_cost,
            notes=notes,
        )
        messages.success(request, f"Item BOM '{name}' berhasil ditambahkan.")
    return redirect("project_detail", uuid=project.uuid)


def bom_item_update(request, uuid):
    item = get_object_or_404(BOMItem, uuid=uuid)
    if request.method == "POST":
        name = request.POST.get("name", item.name).strip()
        item_type = request.POST.get("item_type", item.item_type)
        raw_material_uuid = request.POST.get("raw_material_uuid", "").strip()
        raw_material = RawMaterial.objects.filter(uuid=raw_material_uuid).first() if raw_material_uuid else item.raw_material

        unit = request.POST.get("unit", item.unit).strip()

        raw_est_qty = request.POST.get("est_qty", str(item.est_qty)).strip().replace(",", ".")
        try:
            est_qty = Decimal(raw_est_qty or 0)
            if est_qty < 0:
                est_qty = Decimal(0)
        except Exception:
            est_qty = item.est_qty

        raw_est_cost = request.POST.get("est_unit_cost", str(item.est_unit_cost)).strip()
        clean_cost = raw_est_cost.replace("Rp", "").replace("rp", "").replace(" ", "")
        if "," in clean_cost and "." in clean_cost:
            clean_cost = clean_cost.replace(".", "").replace(",", ".")
        elif "." in clean_cost and "," not in clean_cost:
            parts = clean_cost.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                clean_cost = clean_cost.replace(".", "")
        elif "," in clean_cost:
            clean_cost = clean_cost.replace(",", ".")
        try:
            est_unit_cost = Decimal(clean_cost or 0)
            if est_unit_cost < 0:
                est_unit_cost = Decimal(0)
        except Exception:
            est_unit_cost = item.est_unit_cost

        parent_uuid = request.POST.get("parent_uuid") or None
        parent = BOMItem.objects.filter(uuid=parent_uuid, project=item.project).exclude(id=item.id).first() if parent_uuid else None
        notes = request.POST.get("notes", item.notes).strip()

        if name:
            item.name = name
        item.item_type = item_type
        item.raw_material = raw_material
        item.unit = unit
        item.est_qty = est_qty
        item.est_unit_cost = est_unit_cost
        item.parent = parent
        item.notes = notes
        item.save()
        messages.success(request, f"Item BOM '{item.name}' berhasil diperbarui.")
    return redirect("project_detail", uuid=item.project.uuid)


def bom_item_delete(request, uuid):
    item = get_object_or_404(BOMItem, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        if item.children.exists():
            messages.error(request, f"Item '{item.name}' tidak dapat dihapus karena masih memiliki sub-item / komponen di dalamnya. Hapus atau pindahkan sub-item terlebih dahulu.")
            return redirect("project_detail", uuid=project_uuid)

        if item.realizations.exists():
            messages.error(request, f"Item '{item.name}' tidak dapat dihapus karena sudah memiliki riwayat transaksi realisasi pengeluaran.")
            return redirect("project_detail", uuid=project_uuid)

        name = item.name
        item.delete()
        messages.success(request, f"Item BOM '{name}' berhasil dihapus.")
    return redirect("project_detail", uuid=project_uuid)


# =========================================================================
# LABOR CRUD
# =========================================================================
@transaction.atomic
def labor_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        role_name = request.POST.get("role_name", "").strip()
        unit = request.POST.get("unit", "jam").strip()
        est_quantity = _clean_decimal(request.POST.get("est_quantity"), Decimal(1))
        est_rate = _clean_decimal(request.POST.get("est_rate"), Decimal(0))
        act_quantity = _clean_decimal(request.POST.get("act_quantity"), Decimal(0))
        act_rate = _clean_decimal(request.POST.get("act_rate"), Decimal(0))
        notes = request.POST.get("notes", "").strip()

        if not role_name:
            messages.error(request, "Peran / posisi tenaga kerja wajib diisi.")
            return redirect("project_detail", uuid=project.uuid)

        labor = ProjectLabor.objects.create(
            project=project,
            role_name=role_name,
            unit=unit,
            est_quantity=est_quantity,
            est_rate=est_rate,
            act_quantity=act_quantity,
            act_rate=act_rate,
            notes=notes,
        )
        messages.success(request, f"Tenaga kerja '{labor.role_name}' ({est_quantity:g} {unit}) berhasil ditambahkan ke estimasi HPP.")
    return redirect("project_detail", uuid=project.uuid)


@transaction.atomic
def labor_update(request, uuid):
    item = get_object_or_404(ProjectLabor, uuid=uuid)
    if request.method == "POST":
        role_name = request.POST.get("role_name", "").strip()
        if role_name:
            item.role_name = role_name
        item.unit = request.POST.get("unit", item.unit).strip()
        item.est_quantity = _clean_decimal(request.POST.get("est_quantity"), item.est_quantity)
        item.est_rate = _clean_decimal(request.POST.get("est_rate"), item.est_rate)
        item.act_quantity = _clean_decimal(request.POST.get("act_quantity"), item.act_quantity)
        item.act_rate = _clean_decimal(request.POST.get("act_rate"), item.act_rate)
        item.notes = request.POST.get("notes", item.notes).strip()
        item.save()
        messages.success(request, f"Data tenaga kerja '{item.role_name}' berhasil diperbarui.")
    return redirect("project_detail", uuid=item.project.uuid)


def labor_delete(request, uuid):
    item = get_object_or_404(ProjectLabor, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        if item.realizations.exists():
            messages.error(request, f"Tenaga kerja '{item.role_name}' tidak dapat dihapus karena sudah memiliki riwayat realisasi.")
            return redirect("project_detail", uuid=project_uuid)
        role = item.role_name
        item.delete()
        messages.success(request, f"Tenaga kerja '{role}' berhasil dihapus.")
    return redirect("project_detail", uuid=project_uuid)


# =========================================================================
# OVERHEAD CRUD
# =========================================================================
@transaction.atomic
def overhead_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        est_cost = _clean_decimal(request.POST.get("est_cost"), Decimal(0))
        act_cost = _clean_decimal(request.POST.get("act_cost"), Decimal(0))
        notes = request.POST.get("notes", "").strip()

        if not name:
            messages.error(request, "Deskripsi pos biaya overhead wajib diisi.")
            return redirect("project_detail", uuid=project.uuid)

        ProjectOverhead.objects.create(
            project=project,
            name=name,
            est_cost=est_cost,
            act_cost=act_cost,
            notes=notes,
        )
        messages.success(request, f"Biaya overhead '{name}' (Rp {est_cost:,.0f}) berhasil ditambahkan ke estimasi HPP.")
    return redirect("project_detail", uuid=project.uuid)


@transaction.atomic
def overhead_update(request, uuid):
    item = get_object_or_404(ProjectOverhead, uuid=uuid)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            item.name = name
        item.est_cost = _clean_decimal(request.POST.get("est_cost"), item.est_cost)
        item.act_cost = _clean_decimal(request.POST.get("act_cost"), item.act_cost)
        item.notes = request.POST.get("notes", item.notes).strip()
        item.save()
        messages.success(request, f"Biaya overhead '{item.name}' berhasil diperbarui.")
    return redirect("project_detail", uuid=item.project.uuid)


def overhead_delete(request, uuid):
    item = get_object_or_404(ProjectOverhead, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        if item.realizations.exists():
            messages.error(request, f"Biaya overhead '{item.name}' tidak dapat dihapus karena sudah memiliki riwayat realisasi.")
            return redirect("project_detail", uuid=project_uuid)
        name = item.name
        item.delete()
        messages.success(request, f"Biaya overhead '{name}' berhasil dihapus.")
    return redirect("project_detail", uuid=project_uuid)


# =========================================================================
# PROJECT FINISHED GOODS (Barang Jadi Penyusun Project)
# =========================================================================
@transaction.atomic
def project_fg_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        fg_uuid = request.POST.get("finished_good_uuid", "").strip()
        fg = FinishedGood.objects.filter(uuid=fg_uuid).first() if fg_uuid else None
        if not fg:
            messages.error(request, "Barang jadi yang dipilih tidak valid.")
            return redirect("project_detail", uuid=project.uuid)

        est_qty = _clean_decimal(request.POST.get("est_qty"), Decimal(1))
        est_unit_cost = _clean_decimal(request.POST.get("est_unit_cost"), fg.standard_cost)
        act_qty = _clean_decimal(request.POST.get("act_qty"), Decimal(0))
        act_unit_cost = _clean_decimal(request.POST.get("act_unit_cost"), fg.standard_cost)
        notes = request.POST.get("notes", "").strip()

        if est_qty <= 0:
            messages.error(request, "Kuantitas estimasi barang jadi harus lebih besar dari 0.")
            return redirect("project_detail", uuid=project.uuid)

        # Cek apakah sudah ada barang jadi yang sama di project ini
        existing = ProjectFinishedGood.objects.filter(project=project, finished_good=fg).first()
        if existing:
            existing.est_qty += est_qty
            if est_unit_cost > 0:
                existing.est_unit_cost = est_unit_cost
            if notes:
                existing.notes = f"{existing.notes}; {notes}".strip("; ")
            existing.save()
            messages.success(request, f"Kuantitas barang jadi '{fg.name}' diperbarui menjadi {existing.est_qty:g} {fg.unit}.")
        else:
            ProjectFinishedGood.objects.create(
                project=project,
                finished_good=fg,
                est_qty=est_qty,
                est_unit_cost=est_unit_cost,
                act_qty=act_qty,
                act_unit_cost=act_unit_cost,
                notes=notes,
            )
            messages.success(request, f"Barang jadi '{fg.name}' ({est_qty:g} {fg.unit}) berhasil ditambahkan ke project.")
    return redirect("project_detail", uuid=project.uuid)


@transaction.atomic
def project_fg_update(request, uuid):
    item = get_object_or_404(ProjectFinishedGood, uuid=uuid)
    if request.method == "POST":
        fg_uuid = request.POST.get("finished_good_uuid", "").strip()
        if fg_uuid:
            fg = FinishedGood.objects.filter(uuid=fg_uuid).first()
            if fg:
                item.finished_good = fg
        item.est_qty = _clean_decimal(request.POST.get("est_qty"), item.est_qty)
        item.est_unit_cost = _clean_decimal(request.POST.get("est_unit_cost"), item.est_unit_cost)
        item.act_qty = _clean_decimal(request.POST.get("act_qty"), item.act_qty)
        item.act_unit_cost = _clean_decimal(request.POST.get("act_unit_cost"), item.act_unit_cost)
        item.notes = request.POST.get("notes", item.notes).strip()
        item.save()
        messages.success(request, f"Data barang jadi '{item.finished_good.name}' berhasil diperbarui.")
    return redirect("project_detail", uuid=item.project.uuid)


def project_fg_delete(request, uuid):
    item = get_object_or_404(ProjectFinishedGood, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        if item.realizations.exists():
            messages.error(request, f"Barang jadi '{item.finished_good.name}' tidak dapat dihapus karena sudah ada riwayat pemakaian riil.")
            return redirect("project_detail", uuid=project_uuid)
        name = item.finished_good.name
        item.delete()
        messages.success(request, f"Barang jadi '{name}' berhasil dihapus dari project.")
    return redirect("project_detail", uuid=project_uuid)


# =========================================================================
# STOCK MANAGEMENT & MUTASI BARANG JADI
# =========================================================================
def stock_report(request):
    """
    Laporan Rekap Stock Semua Barang Jadi
    """
    query = request.GET.get("q", "").strip()
    finished_goods = FinishedGood.objects.all().order_by("sku")
    if query:
        finished_goods = finished_goods.filter(Q(name__icontains=query) | Q(sku__icontains=query))

    total_units = sum(fg.current_stock for fg in finished_goods)
    total_valuation = sum(fg.current_stock * fg.standard_cost for fg in finished_goods)

    for fg in finished_goods:
        fg.stock_valuation = fg.current_stock * fg.standard_cost
        fg.has_transactions = fg.mutations.exists() or fg.project_usages.exists()

    return render(request, "hpp/stock_report.html", {
        "finished_goods": finished_goods,
        "total_units": total_units,
        "total_valuation": total_valuation,
        "query": query,
    })


def finished_good_create(request):
    if request.method == "POST":
        sku = request.POST.get("sku", "").strip()
        name = request.POST.get("name", "").strip()
        unit = request.POST.get("unit", "unit").strip()
        standard_cost = Decimal(request.POST.get("standard_cost") or 0)
        initial_stock = Decimal(request.POST.get("initial_stock") or 0)
        notes = request.POST.get("notes", "")

        fg = FinishedGood.objects.create(
            sku=sku,
            name=name,
            unit=unit,
            standard_cost=standard_cost,
            current_stock=initial_stock,
            notes=notes,
        )

        if initial_stock > 0:
            FinishedGoodStockMutation.objects.create(
                finished_good=fg,
                mutation_type="IN",
                quantity=initial_stock,
                balance_after=initial_stock,
                reference_no="INITIAL-STOCK",
                notes="Saldo awal barang jadi"
            )

        return redirect("stock_report")
    return render(request, "hpp/finished_good_form.html")


def stock_card(request, uuid):
    """
    Kartu Stock per Barang Jadi -> Delegasi ke views_finished_good
    """
    return views_finished_good.finished_good_stock_card(request, uuid)


def stock_mutation_create(request, uuid):
    """
    Manual Stock IN / OUT (Penyesuaian / Restock Pabrik)
    """
    fg = get_object_or_404(FinishedGood, uuid=uuid)
    if request.method == "POST":
        mutation_type = request.POST.get("mutation_type")  # IN / OUT
        quantity = Decimal(request.POST.get("quantity") or 0)
        reference_no = request.POST.get("reference_no", "").strip()
        notes = request.POST.get("notes", "").strip()

        if quantity > 0:
            if mutation_type == "IN":
                fg.current_stock += quantity
            elif mutation_type == "OUT":
                fg.current_stock -= quantity
            fg.save()

            FinishedGoodStockMutation.objects.create(
                finished_good=fg,
                mutation_type=mutation_type,
                quantity=quantity,
                balance_after=fg.current_stock,
                reference_no=reference_no or "MANUAL-ADJ",
                notes=notes,
            )

    return redirect("stock_card", uuid=fg.uuid)


# =========================================================================
# EXPORT & PRINT
# =========================================================================
def export_project_excel(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "HPP & BOM"

    bold_font = Font(bold=True)
    header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    sec_fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")

    ws.append(["LAPORAN HPP & BOM PROJECT"])
    ws["A1"].font = Font(size=14, bold=True)
    ws.append([])

    ws.append(["Kode Project", project.code, "Status", project.get_status_display()])
    ws.append(["Nama Project", project.name, "Progress", f"{project.progress_percentage}%"])
    ws.append(["Customer", project.customer_name or "-", "Nilai Kontrak", float(project.contract_value)])
    ws.append([])

    # 1. BOM Materials
    ws.append(["1. BILL OF MATERIALS (BOM)"])
    ws.cell(row=ws.max_row, column=1).fill = sec_fill
    ws.append(["Tipe", "Item / Part", "Satuan", "Est Qty", "Est Harga", "Est Total", "Real Qty", "Real Harga", "Real Total", "Selisih"])
    for col in range(1, 11):
        ws.cell(row=ws.max_row, column=col).fill = header_fill
        ws.cell(row=ws.max_row, column=col).font = bold_font

    for m in project.bom_items.all():
        diff = float(m.act_total - m.est_total)
        ws.append([
            m.get_item_type_display(),
            m.name,
            m.unit,
            float(m.est_qty),
            float(m.est_unit_cost),
            float(m.est_total),
            float(m.act_qty),
            float(m.act_unit_cost),
            float(m.act_total),
            diff
        ])
    ws.append(["Subtotal Material", "", "", "", "", float(project.total_est_material), "", "", float(project.total_act_material), float(project.total_act_material - project.total_est_material)])
    ws.cell(row=ws.max_row, column=1).font = bold_font
    ws.append([])

    # 2. Labor
    ws.append(["2. BIAYA TENAGA KERJA (LABOR)"])
    ws.cell(row=ws.max_row, column=1).fill = sec_fill
    ws.append(["Peran / Posisi", "Satuan", "Est Qty/Jam", "Est Tarif", "Est Total", "Real Qty/Jam", "Real Tarif", "Real Total", "Selisih"])
    for col in range(1, 10):
        ws.cell(row=ws.max_row, column=col).fill = header_fill
        ws.cell(row=ws.max_row, column=col).font = bold_font

    for l in project.labor_items.all():
        diff = float(l.act_total - l.est_total)
        ws.append([
            l.role_name,
            l.unit,
            float(l.est_quantity),
            float(l.est_rate),
            float(l.est_total),
            float(l.act_quantity),
            float(l.act_rate),
            float(l.act_total),
            diff
        ])
    ws.append(["Subtotal Tenaga", "", "", "", float(project.total_est_labor), "", "", float(project.total_act_labor), float(project.total_act_labor - project.total_est_labor)])
    ws.cell(row=ws.max_row, column=1).font = bold_font
    ws.append([])

    # 3. Finished Goods
    ws.append(["3. BARANG JADI (FINISHED GOODS)"])
    ws.cell(row=ws.max_row, column=1).fill = sec_fill
    ws.append(["SKU & Nama Barang Jadi", "Satuan", "Est Qty", "Est Harga", "Est Total", "Real Qty", "Real Harga", "Real Total", "Selisih"])
    for col in range(1, 10):
        ws.cell(row=ws.max_row, column=col).fill = header_fill
        ws.cell(row=ws.max_row, column=col).font = bold_font

    for fg in project.finished_good_items.all():
        diff = float(fg.act_total - fg.est_total)
        ws.append([
            f"[{fg.finished_good.sku}] {fg.finished_good.name}",
            fg.finished_good.unit,
            float(fg.est_qty),
            float(fg.est_unit_cost),
            float(fg.est_total),
            float(fg.act_qty),
            float(fg.act_unit_cost),
            float(fg.act_total),
            diff
        ])
    ws.append(["Subtotal Barang Jadi", "", "", "", float(project.total_est_finished_goods), "", "", float(project.total_act_finished_goods), float(project.total_act_finished_goods - project.total_est_finished_goods)])
    ws.cell(row=ws.max_row, column=1).font = bold_font
    ws.append([])

    # 4. Overhead
    ws.append(["4. BIAYA OVERHEAD & LAINNYA"])
    ws.cell(row=ws.max_row, column=1).fill = sec_fill
    ws.append(["Deskripsi Biaya", "Est Biaya", "Real Biaya", "Selisih"])
    for col in range(1, 5):
        ws.cell(row=ws.max_row, column=col).fill = header_fill
        ws.cell(row=ws.max_row, column=col).font = bold_font

    for o in project.overhead_items.all():
        diff = float(o.act_cost - o.est_cost)
        ws.append([
            o.name,
            float(o.est_cost),
            float(o.act_cost),
            diff
        ])
    ws.append(["Subtotal Overhead", float(project.total_est_overhead), float(project.total_act_overhead), float(project.total_act_overhead - project.total_est_overhead)])
    ws.cell(row=ws.max_row, column=1).font = bold_font
    ws.append([])

    # Summary
    ws.append(["RINGKASAN HPP & MARGIN"])
    ws.cell(row=ws.max_row, column=1).font = bold_font
    ws.append(["Komponen", "Estimasi (Rp)", "Realisasi (Rp)", "Deviasi (Rp)"])
    ws.append(["TOTAL HPP", float(project.total_hpp_estimated), float(project.total_hpp_actual), float(project.total_hpp_actual - project.total_hpp_estimated)])
    ws.append(["Nilai Kontrak / Penjualan", float(project.contract_value), float(project.contract_value), 0])
    ws.append(["Gross Profit", float(project.est_gross_profit), float(project.act_gross_profit), float(project.act_gross_profit - project.est_gross_profit)])
    ws.append(["Margin (%)", f"{project.est_margin_pct:.2f}%", f"{project.act_margin_pct:.2f}%", "-"])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="HPP_{project.code}.xlsx"'
    wb.save(response)
    return response


def print_project_pdf(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    return render(request, "hpp/project_print.html", {
        "project": project,
        "materials": project.bom_items.all(),
        "labors": project.labor_items.all(),
        "overheads": project.overhead_items.all(),
        "finished_goods": project.finished_good_items.all(),
    })

def finished_good_update(request, uuid):
    fg = get_object_or_404(FinishedGood, uuid=uuid)
    if request.method == "POST":
        fg.sku = request.POST.get("sku", fg.sku).strip()
        fg.name = request.POST.get("name", fg.name).strip()
        fg.unit = request.POST.get("unit", fg.unit).strip()
        fg.standard_cost = Decimal(request.POST.get("standard_cost") or 0)
        fg.notes = request.POST.get("notes", fg.notes)
        fg.save()
    return redirect("stock_report")


def finished_good_delete(request, uuid):
    fg = get_object_or_404(FinishedGood, uuid=uuid)
    if request.method == "POST":
        has_mutations = fg.mutations.exists()
        has_projects = fg.project_usages.exists()

        if has_mutations or has_projects:
            # Tidak boleh dihapus jika ada transaksi / relasi project
            from django.contrib import messages
            messages.error(request, f"Barang Jadi '{fg.name}' tidak dapat dihapus karena sudah memiliki riwayat mutasi / transaksi project.")
        else:
            fg.delete()
            from django.contrib import messages
            messages.success(request, f"Barang Jadi '{fg.name}' berhasil dihapus.")
    return redirect("stock_report")


# =========================================================================
# ABSENSI & KARYAWAN VIEWS
# =========================================================================
from datetime import date, datetime


def attendance_list(request):
    """
    Halaman Rekap Absensi Karyawan
    """
    selected_date_str = request.GET.get("date", "").strip()
    status_filter = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()

    if selected_date_str:
        try:
            filter_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            filter_date = date.today()
    else:
        filter_date = date.today()

    attendances = Attendance.objects.filter(date=filter_date).select_related("employee")
    if status_filter:
        attendances = attendances.filter(status=status_filter)
    if query:
        attendances = attendances.filter(Q(employee__name__icontains=query) | Q(employee__nik__icontains=query))

    employees = Employee.objects.filter(is_active=True).order_by("name")

    # Summary KPI
    all_day_records = Attendance.objects.filter(date=filter_date)
    total_hadir = all_day_records.filter(status="HADIR").count()
    total_ijin = all_day_records.filter(status="IJIN").count()
    total_sakit = all_day_records.filter(status="SAKIT").count()
    total_alpha = all_day_records.filter(status="ALPHA").count()
    total_ot_hours = sum(a.overtime_hours for a in all_day_records)
    total_wage_day = sum(a.wage for a in all_day_records)

    return render(request, "hpp/attendance_list.html", {
        "attendances": attendances,
        "employees": employees,
        "selected_date": filter_date.strftime("%Y-%m-%d"),
        "status_filter": status_filter,
        "query": query,
        "status_choices": Attendance.STATUS_CHOICES,
        "total_hadir": total_hadir,
        "total_ijin": total_ijin,
        "total_sakit": total_sakit,
        "total_alpha": total_alpha,
        "total_ot_hours": total_ot_hours,
        "total_wage_day": total_wage_day,
    })


def attendance_create(request):
    if request.method == "POST":
        emp_uuid = request.POST.get("employee_uuid")
        att_date_str = request.POST.get("date") or str(date.today())
        status = request.POST.get("status", "HADIR")
        check_in = request.POST.get("check_in") or None
        check_out = request.POST.get("check_out") or None
        overtime_hours = Decimal(request.POST.get("overtime_hours") or 0)
        notes = request.POST.get("notes", "")

        employee = get_object_or_404(Employee, uuid=emp_uuid)
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()

        Attendance.objects.update_or_create(
            employee=employee,
            date=att_date,
            defaults={
                "status": status,
                "check_in": check_in,
                "check_out": check_out,
                "overtime_hours": overtime_hours,
                "notes": notes,
            }
        )
        messages.success(request, f"Absensi {employee.name} tanggal {att_date} berhasil disimpan.")
        return redirect(f"/attendance/?date={att_date_str}")
    return redirect("attendance_list")


def attendance_update(request, uuid):
    att = get_object_or_404(Attendance, uuid=uuid)
    if request.method == "POST":
        att.status = request.POST.get("status", att.status)
        att.check_in = request.POST.get("check_in") or None
        att.check_out = request.POST.get("check_out") or None
        att.overtime_hours = Decimal(request.POST.get("overtime_hours") or 0)
        att.notes = request.POST.get("notes", att.notes)
        att.save()
        messages.success(request, f"Absensi {att.employee.name} berhasil diperbarui.")
    return redirect(f"/attendance/?date={att.date.strftime('%Y-%m-%d')}")


def attendance_delete(request, uuid):
    att = get_object_or_404(Attendance, uuid=uuid)
    att_date_str = att.date.strftime("%Y-%m-%d")
    if request.method == "POST":
        att.delete()
        messages.success(request, f"Data absensi berhasil dihapus.")
    return redirect(f"/attendance/?date={att_date_str}")


def employee_list(request):
    """
    Daftar Master Karyawan
    """
    employees = Employee.objects.all().order_by("name")
    return render(request, "hpp/employee_list.html", {
        "employees": employees,
    })


def employee_create(request):
    if request.method == "POST":
        nik = request.POST.get("nik", "").strip()
        name = request.POST.get("name", "").strip()
        position = request.POST.get("position", "Tukang").strip()
        daily_rate = Decimal(request.POST.get("daily_rate") or 0)
        overtime_rate_per_hour = Decimal(request.POST.get("overtime_rate_per_hour") or 0)
        notes = request.POST.get("notes", "")

        Employee.objects.create(
            nik=nik,
            name=name,
            position=position,
            daily_rate=daily_rate,
            overtime_rate_per_hour=overtime_rate_per_hour,
            notes=notes,
        )
        messages.success(request, f"Karyawan {name} berhasil ditambahkan.")
    return redirect("employee_list")


def employee_update(request, uuid):
    emp = get_object_or_404(Employee, uuid=uuid)
    if request.method == "POST":
        emp.nik = request.POST.get("nik", emp.nik).strip()
        emp.name = request.POST.get("name", emp.name).strip()
        emp.position = request.POST.get("position", emp.position).strip()
        emp.daily_rate = Decimal(request.POST.get("daily_rate") or 0)
        emp.overtime_rate_per_hour = Decimal(request.POST.get("overtime_rate_per_hour") or 0)
        emp.is_active = request.POST.get("is_active") == "on"
        emp.notes = request.POST.get("notes", emp.notes)
        emp.save()
        messages.success(request, f"Data karyawan {emp.name} berhasil diperbarui.")
    return redirect("employee_list")


def employee_delete(request, uuid):
    emp = get_object_or_404(Employee, uuid=uuid)
    if request.method == "POST":
        if emp.attendances.exists():
            messages.error(request, f"Karyawan {emp.name} tidak dapat dihapus karena memiliki riwayat absensi. Silakan nonaktifkan statusnya.")
        else:
            emp.delete()
            messages.success(request, f"Karyawan {emp.name} berhasil dihapus.")
    return redirect("employee_list")


# =========================================================================
# KINERJA KARYAWAN (WORK LOGS) VIEWS
# =========================================================================
def work_log_list(request):
    """
    Daftar Log Kinerja & Kegiatan Harian Karyawan
    """
    selected_date_str = request.GET.get("date", "").strip()
    emp_uuid = request.GET.get("employee", "").strip()
    status_filter = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()

    logs = EmployeeWorkLog.objects.all().select_related("employee", "project")

    if selected_date_str:
        try:
            filter_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
            logs = logs.filter(date=filter_date)
        except ValueError:
            pass

    if emp_uuid:
        logs = logs.filter(employee__uuid=emp_uuid)

    if status_filter:
        logs = logs.filter(status=status_filter)

    if query:
        logs = logs.filter(
            Q(task_description__icontains=query) |
            Q(activity_category__icontains=query) |
            Q(employee__name__icontains=query) |
            Q(project__name__icontains=query)
        )

    employees = Employee.objects.filter(is_active=True).order_by("name")
    projects = Project.objects.all().order_by("-created_at")

    total_logs = logs.count()
    total_hours = sum(l.hours_spent for l in logs)
    completed_count = logs.filter(status="completed").count()

    return render(request, "hpp/work_log_list.html", {
        "logs": logs,
        "employees": employees,
        "projects": projects,
        "selected_date": selected_date_str,
        "selected_emp": emp_uuid,
        "selected_status": status_filter,
        "query": query,
        "status_choices": EmployeeWorkLog.STATUS_CHOICES,
        "rating_choices": EmployeeWorkLog.RATING_CHOICES,
        "total_logs": total_logs,
        "total_hours": total_hours,
        "completed_count": completed_count,
    })


def work_log_create(request):
    if request.method == "POST":
        emp_uuid = request.POST.get("employee_uuid")
        proj_uuid = request.POST.get("project_uuid") or None
        date_str = request.POST.get("date") or str(date.today())
        activity_category = request.POST.get("activity_category", "Produksi / Fabrikasi").strip()
        task_description = request.POST.get("task_description", "").strip()
        output_qty = Decimal(request.POST.get("output_qty") or 0)
        output_unit = request.POST.get("output_unit", "unit").strip()
        hours_spent = Decimal(request.POST.get("hours_spent") or 8)
        status = request.POST.get("status", "completed")
        obstacles = request.POST.get("obstacles", "").strip()
        supervisor_rating = int(request.POST.get("supervisor_rating") or 4)

        employee = get_object_or_404(Employee, uuid=emp_uuid)
        project = Project.objects.filter(uuid=proj_uuid).first() if proj_uuid else None
        log_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        EmployeeWorkLog.objects.create(
            employee=employee,
            project=project,
            date=log_date,
            activity_category=activity_category,
            task_description=task_description,
            output_qty=output_qty,
            output_unit=output_unit,
            hours_spent=hours_spent,
            status=status,
            obstacles=obstacles,
            supervisor_rating=supervisor_rating,
        )
        messages.success(request, f"Log kegiatan {employee.name} berhasil disimpan.")
    return redirect("work_log_list")


def work_log_update(request, uuid):
    log = get_object_or_404(EmployeeWorkLog, uuid=uuid)
    if request.method == "POST":
        proj_uuid = request.POST.get("project_uuid") or None
        date_str = request.POST.get("date") or str(log.date)
        log.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        log.project = Project.objects.filter(uuid=proj_uuid).first() if proj_uuid else None
        log.activity_category = request.POST.get("activity_category", log.activity_category).strip()
        log.task_description = request.POST.get("task_description", log.task_description).strip()
        log.output_qty = Decimal(request.POST.get("output_qty") or 0)
        log.output_unit = request.POST.get("output_unit", log.output_unit).strip()
        log.hours_spent = Decimal(request.POST.get("hours_spent") or 8)
        log.status = request.POST.get("status", log.status)
        log.obstacles = request.POST.get("obstacles", log.obstacles).strip()
        log.supervisor_rating = int(request.POST.get("supervisor_rating") or log.supervisor_rating)
        log.save()
        messages.success(request, f"Log kegiatan {log.employee.name} berhasil diperbarui.")
    return redirect("work_log_list")


def work_log_delete(request, uuid):
    log = get_object_or_404(EmployeeWorkLog, uuid=uuid)
    if request.method == "POST":
        log.delete()
        messages.success(request, f"Log kegiatan berhasil dihapus.")
    return redirect("work_log_list")


# =========================================================================
# MUTASI BARANG JADI & KARTU STOCK DEDICATED VIEWS
# =========================================================================
from . import views_finished_good

def stock_mutation_list(request):
    """Delegasi ke modul views_finished_good"""
    return views_finished_good.finished_good_mutation_list(request)


def stock_mutation_general_create(request):
    """Delegasi ke modul views_finished_good"""
    return views_finished_good.finished_good_mutation_create(request)


def stock_card_index(request):
    """
    Menu Kartu Stock Standalone -> Delegasi ke views_finished_good
    """
    return views_finished_good.finished_good_stock_card_index(request)


def finished_good_form_view(request):
    """
    Halaman Form Tambah Barang Jadi
    """
    if request.method == "POST":
        sku = request.POST.get("sku", "").strip()
        name = request.POST.get("name", "").strip()
        unit = request.POST.get("unit", "unit").strip()
        standard_cost = Decimal(request.POST.get("standard_cost") or 0)
        initial_stock = Decimal(request.POST.get("initial_stock") or 0)
        notes = request.POST.get("notes", "")

        if FinishedGood.objects.filter(sku=sku).exists():
            messages.error(request, f"SKU {sku} sudah terdaftar.")
            return render(request, "hpp/finished_good_form.html")

        fg = FinishedGood.objects.create(
            sku=sku,
            name=name,
            unit=unit,
            standard_cost=standard_cost,
            current_stock=initial_stock,
            notes=notes,
        )

        if initial_stock > 0:
            FinishedGoodStockMutation.objects.create(
                finished_good=fg,
                mutation_type="IN",
                quantity=initial_stock,
                balance_after=initial_stock,
                reference_no=f"INIT-{fg.sku}",
                notes="Saldo stock awal"
            )
        messages.success(request, f"Barang Jadi '{name}' berhasil ditambahkan.")
        return redirect("stock_report")

    return render(request, "hpp/finished_good_form.html")
