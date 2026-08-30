from .utils import generate_project_code, get_ordered_bom
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal
import openpyxl
from openpyxl.styles import Font, PatternFill

from .models import (
    UnitMaster,
    Customer,
    Employee, Attendance, EmployeeWorkLog,
    Project, BOMItem, ProjectLabor, ProjectOverhead,
    MaterialMaster, LaborMaster, FinishedGood,
    ProjectFinishedGood, FinishedGoodStockMutation
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


def project_create(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip() or generate_project_code()
        name = request.POST.get("name")
        customer_uuid = request.POST.get("customer_uuid", "").strip()
        customer = Customer.objects.filter(uuid=customer_uuid).first() if customer_uuid else None
        customer_name = str(customer) if customer else request.POST.get("customer_name", "")
        contract_value = Decimal(request.POST.get("contract_value") or 0)
        progress_percentage = int(request.POST.get("progress_percentage") or 0)
        status = request.POST.get("status", "draft")
        start_date = request.POST.get("start_date") or None
        target_date = request.POST.get("target_date") or None

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
        )
        project.release_stock_if_completed()
        return redirect("project_detail", uuid=project.uuid)

    auto_code = generate_project_code()
    customers = Customer.objects.all().order_by("name")
    return render(request, "hpp/project_form.html", {
        "status_choices": Project.STATUS_CHOICES,
        "auto_code": auto_code,
        "customers": customers,
    })


def project_detail(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    materials = get_ordered_bom(project)
    labors = project.labor_items.all().select_related("labor_master")
    overheads = project.overhead_items.all()
    finished_goods = project.finished_good_items.all().select_related("finished_good")
    
    master_materials = MaterialMaster.objects.all().order_by("name")
    master_labors = LaborMaster.objects.all().order_by("role_name")
    master_finished_goods = FinishedGood.objects.all().order_by("name")

    return render(request, "hpp/project_detail.html", {
        "project": project,
        "materials": materials,
        "labors": labors,
        "overheads": overheads,
        "finished_goods": finished_goods,
        "master_materials": master_materials,
        "master_labors": master_labors,
        "master_finished_goods": master_finished_goods,
        "status_choices": Project.STATUS_CHOICES,
    })


def project_update(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    if request.method == "POST":
        project.code = request.POST.get("code", project.code)
        project.name = request.POST.get("name", project.name)
        project.customer_name = request.POST.get("customer_name", "")
        project.contract_value = Decimal(request.POST.get("contract_value") or 0)
        project.progress_percentage = int(request.POST.get("progress_percentage") or 0)
        project.status = request.POST.get("status", project.status)
        project.start_date = request.POST.get("start_date") or None
        project.target_date = request.POST.get("target_date") or None
        project.save()
        
        # Cek trigger potong stock jika project selesai
        project.release_stock_if_completed()
    return redirect("project_detail", uuid=project.uuid)


# =========================================================================
# BOM CRUD
# =========================================================================
def bom_item_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        item_type = request.POST.get("item_type", "material")
        unit = request.POST.get("unit", "pcs").strip()
        est_qty = Decimal(request.POST.get("est_qty") or 0)
        est_unit_cost = Decimal(request.POST.get("est_unit_cost") or 0)
        act_qty = Decimal(request.POST.get("act_qty") or 0)
        act_unit_cost = Decimal(request.POST.get("act_unit_cost") or 0)
        parent_uuid = request.POST.get("parent_uuid") or None
        notes = request.POST.get("notes", "")

        parent = BOMItem.objects.filter(uuid=parent_uuid, project=project).first() if parent_uuid else None

        BOMItem.objects.create(
            project=project,
            parent=parent,
            name=name,
            item_type=item_type,
            unit=unit,
            est_qty=est_qty,
            est_unit_cost=est_unit_cost,
            act_qty=act_qty,
            act_unit_cost=act_unit_cost,
            notes=notes,
        )
    return redirect("project_detail", uuid=project.uuid)


def bom_item_update(request, uuid):
    item = get_object_or_404(BOMItem, uuid=uuid)
    if request.method == "POST":
        item.name = request.POST.get("name", item.name).strip()
        item.item_type = request.POST.get("item_type", item.item_type)
        item.unit = request.POST.get("unit", item.unit).strip()
        item.est_qty = Decimal(request.POST.get("est_qty") or 0)
        item.est_unit_cost = Decimal(request.POST.get("est_unit_cost") or 0)
        item.act_qty = Decimal(request.POST.get("act_qty") or 0)
        item.act_unit_cost = Decimal(request.POST.get("act_unit_cost") or 0)
        parent_uuid = request.POST.get("parent_uuid") or None
        item.parent = BOMItem.objects.filter(uuid=parent_uuid, project=item.project).exclude(id=item.id).first() if parent_uuid else None
        item.notes = request.POST.get("notes", item.notes)
        item.save()
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
def labor_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        role_name = request.POST.get("role_name", "").strip()
        unit = request.POST.get("unit", "jam").strip()
        est_quantity = Decimal(request.POST.get("est_quantity") or 0)
        est_rate = Decimal(request.POST.get("est_rate") or 0)
        act_quantity = Decimal(request.POST.get("act_quantity") or 0)
        act_rate = Decimal(request.POST.get("act_rate") or 0)
        notes = request.POST.get("notes", "")

        ProjectLabor.objects.create(
            project=project,
            role_name=role_name,
            unit=unit,
            est_quantity=est_quantity,
            est_rate=est_rate,
            act_quantity=act_quantity,
            act_rate=act_rate,
            notes=notes,
        )
    return redirect("project_detail", uuid=project.uuid)


def labor_update(request, uuid):
    item = get_object_or_404(ProjectLabor, uuid=uuid)
    if request.method == "POST":
        item.role_name = request.POST.get("role_name", item.role_name).strip()
        item.unit = request.POST.get("unit", item.unit).strip()
        item.est_quantity = Decimal(request.POST.get("est_quantity") or 0)
        item.est_rate = Decimal(request.POST.get("est_rate") or 0)
        item.act_quantity = Decimal(request.POST.get("act_quantity") or 0)
        item.act_rate = Decimal(request.POST.get("act_rate") or 0)
        item.notes = request.POST.get("notes", item.notes)
        item.save()
    return redirect("project_detail", uuid=item.project.uuid)


def labor_delete(request, uuid):
    item = get_object_or_404(ProjectLabor, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        item.delete()
    return redirect("project_detail", uuid=project_uuid)


# =========================================================================
# OVERHEAD CRUD
# =========================================================================
def overhead_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        est_cost = Decimal(request.POST.get("est_cost") or 0)
        act_cost = Decimal(request.POST.get("act_cost") or 0)
        notes = request.POST.get("notes", "")

        ProjectOverhead.objects.create(
            project=project,
            name=name,
            est_cost=est_cost,
            act_cost=act_cost,
            notes=notes,
        )
    return redirect("project_detail", uuid=project.uuid)


def overhead_update(request, uuid):
    item = get_object_or_404(ProjectOverhead, uuid=uuid)
    if request.method == "POST":
        item.name = request.POST.get("name", item.name).strip()
        item.est_cost = Decimal(request.POST.get("est_cost") or 0)
        item.act_cost = Decimal(request.POST.get("act_cost") or 0)
        item.notes = request.POST.get("notes", item.notes)
        item.save()
    return redirect("project_detail", uuid=item.project.uuid)


def overhead_delete(request, uuid):
    item = get_object_or_404(ProjectOverhead, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        item.delete()
    return redirect("project_detail", uuid=project_uuid)


# =========================================================================
# PROJECT FINISHED GOODS (Barang Jadi Penyusun Project)
# =========================================================================
def project_fg_add(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    if request.method == "POST":
        fg_uuid = request.POST.get("finished_good_uuid")
        fg = get_object_or_404(FinishedGood, uuid=fg_uuid)
        est_qty = Decimal(request.POST.get("est_qty") or 0)
        est_unit_cost = Decimal(request.POST.get("est_unit_cost") or fg.standard_cost or 0)
        act_qty = Decimal(request.POST.get("act_qty") or 0)
        act_unit_cost = Decimal(request.POST.get("act_unit_cost") or fg.standard_cost or 0)
        notes = request.POST.get("notes", "")

        ProjectFinishedGood.objects.create(
            project=project,
            finished_good=fg,
            est_qty=est_qty,
            est_unit_cost=est_unit_cost,
            act_qty=act_qty,
            act_unit_cost=act_unit_cost,
            notes=notes,
        )
    return redirect("project_detail", uuid=project.uuid)


def project_fg_update(request, uuid):
    item = get_object_or_404(ProjectFinishedGood, uuid=uuid)
    if request.method == "POST":
        fg_uuid = request.POST.get("finished_good_uuid")
        if fg_uuid:
            item.finished_good = get_object_or_404(FinishedGood, uuid=fg_uuid)
        item.est_qty = Decimal(request.POST.get("est_qty") or 0)
        item.est_unit_cost = Decimal(request.POST.get("est_unit_cost") or 0)
        item.act_qty = Decimal(request.POST.get("act_qty") or 0)
        item.act_unit_cost = Decimal(request.POST.get("act_unit_cost") or 0)
        item.notes = request.POST.get("notes", item.notes)
        item.save()
    return redirect("project_detail", uuid=item.project.uuid)


def project_fg_delete(request, uuid):
    item = get_object_or_404(ProjectFinishedGood, uuid=uuid)
    project_uuid = item.project.uuid
    if request.method == "POST":
        item.delete()
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
    Kartu Stock per Barang Jadi
    """
    fg = get_object_or_404(FinishedGood, uuid=uuid)
    mutations = fg.mutations.all().select_related("project")

    return render(request, "hpp/stock_card.html", {
        "finished_good": fg,
        "mutations": mutations,
    })


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
def stock_mutation_list(request):
    """
    Halaman Menu Mutasi Barang Jadi (Pencatatan Barang Masuk, Rusak, Penyesuaian)
    """
    mutations = FinishedGoodStockMutation.objects.all().select_related("finished_good", "project")
    fg_uuid = request.GET.get("fg", "").strip()
    mutation_type = request.GET.get("type", "").strip()
    query = request.GET.get("q", "").strip()

    if fg_uuid:
        mutations = mutations.filter(finished_good__uuid=fg_uuid)
    if mutation_type:
        mutations = mutations.filter(mutation_type=mutation_type)
    if query:
        mutations = mutations.filter(
            Q(reference_no__icontains=query) |
            Q(notes__icontains=query) |
            Q(finished_good__name__icontains=query) |
            Q(finished_good__sku__icontains=query)
        )

    finished_goods = FinishedGood.objects.all().order_by("name")

    return render(request, "hpp/stock_mutation_list.html", {
        "mutations": mutations,
        "finished_goods": finished_goods,
        "selected_fg": fg_uuid,
        "selected_type": mutation_type,
        "query": query,
    })


def stock_mutation_general_create(request):
    """
    Input transaksi mutasi barang masuk, barang rusak, atau penyesuaian
    """
    if request.method == "POST":
        fg_uuid = request.POST.get("finished_good_uuid")
        mutation_type = request.POST.get("mutation_type", "IN")  # IN atau OUT
        reason_type = request.POST.get("reason_type", "masuk")   # masuk, rusak, koreksi
        quantity = Decimal(request.POST.get("quantity") or 0)
        reference_no = request.POST.get("reference_no", "").strip()
        notes = request.POST.get("notes", "").strip()

        fg = get_object_or_404(FinishedGood, uuid=fg_uuid)

        if quantity <= 0:
            messages.error(request, "Jumlah mutasi harus lebih besar dari 0.")
            return redirect("stock_mutation_list")

        # Tentukan arah mutasi
        if mutation_type == "IN":
            fg.current_stock += quantity
            prefix = "[MASUK]"
        else:
            if fg.current_stock < quantity:
                messages.error(request, f"Stock {fg.name} tidak mencukupi (Tersedia: {fg.current_stock} {fg.unit}).")
                return redirect("stock_mutation_list")
            fg.current_stock -= quantity
            prefix = "[RUSAK/OUT]" if reason_type == "rusak" else "[KOREKSI/OUT]"

        fg.save()

        full_notes = f"{prefix} {notes}".strip()
        FinishedGoodStockMutation.objects.create(
            finished_good=fg,
            mutation_type=mutation_type,
            quantity=quantity,
            balance_after=fg.current_stock,
            reference_no=reference_no or f"MUT-{fg.sku}",
            notes=full_notes
        )
        messages.success(request, f"Mutasi stock {fg.name} ({mutation_type} {quantity} {fg.unit}) berhasil dicatat.")
    return redirect("stock_mutation_list")


def stock_card_index(request):
    """
    Menu Kartu Stock Standalone (dengan filter pemilih barang jadi)
    """
    finished_goods = FinishedGood.objects.all().order_by("name")
    selected_fg_uuid = request.GET.get("fg", "").strip()

    if selected_fg_uuid:
        selected_fg = FinishedGood.objects.filter(uuid=selected_fg_uuid).first()
    else:
        selected_fg = finished_goods.first()

    mutations = []
    total_in = 0
    total_out = 0

    if selected_fg:
        mutations = selected_fg.mutations.all().select_related("project")
        total_in = sum(m.quantity for m in mutations if m.mutation_type == "IN")
        total_out = sum(m.quantity for m in mutations if m.mutation_type == "OUT")

    return render(request, "hpp/stock_card_index.html", {
        "finished_goods": finished_goods,
        "selected_fg": selected_fg,
        "mutations": mutations,
        "total_in": total_in,
        "total_out": total_out,
    })


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
