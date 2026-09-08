from django.urls import path
from . import views
from . import views_realization
from . import views_customer
from . import views_raw_material
from . import views_unit
from . import views_finished_good
from . import views_absence_type

urlpatterns = [
    # Project
    path("", views.project_list, name="project_list"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<uuid:uuid>/", views.project_detail, name="project_detail"),
    path("projects/<uuid:uuid>/update/", views.project_update, name="project_update"),
    path("projects/<uuid:uuid>/close/", views.project_close, name="project_close"),
    path("projects/<uuid:uuid>/reopen/", views.project_reopen, name="project_reopen"),
    path("projects/<uuid:uuid>/bap/", views.project_closing_bap, name="project_closing_bap"),
    
    # Master Satuan (Unit Master)
    path("units/", views_unit.unit_list, name="unit_list"),
    path("units/new/", views_unit.unit_create, name="unit_create"),
    path("units/<uuid:uuid>/update/", views_unit.unit_update, name="unit_update"),
    path("units/<uuid:uuid>/delete/", views_unit.unit_delete, name="unit_delete"),

    # Master Customer
    path("customers/", views_customer.customer_list, name="customer_list"),
    path("customers/new/", views_customer.customer_create, name="customer_create"),
    path("customers/<uuid:uuid>/update/", views_customer.customer_update, name="customer_update"),
    path("customers/<uuid:uuid>/delete/", views_customer.customer_delete, name="customer_delete"),

    # Bahan Baku (Raw Material) & Multi-Satuan
    path("raw-materials/", views_raw_material.raw_material_list, name="raw_material_list"),
    path("raw-materials/export/", views_raw_material.raw_material_export_excel, name="raw_material_export_excel"),
    path("raw-materials/new/", views_raw_material.raw_material_create, name="raw_material_create"),
    path("raw-materials/<uuid:uuid>/", views_raw_material.raw_material_detail, name="raw_material_detail"),
    path("raw-materials/<uuid:uuid>/update/", views_raw_material.raw_material_update, name="raw_material_update"),
    path("raw-materials/<uuid:uuid>/delete/", views_raw_material.raw_material_delete, name="raw_material_delete"),
    path("raw-materials/<uuid:material_uuid>/conversions/add/", views_raw_material.raw_material_conversion_add, name="raw_material_conversion_add"),
    path("raw-materials/conversions/<uuid:uuid>/delete/", views_raw_material.raw_material_conversion_delete, name="raw_material_conversion_delete"),
    path("raw-materials/mutations/", views_raw_material.raw_material_stock_mutation_list, name="raw_material_stock_mutation_list"),
    path("raw-materials/mutations/export/", views_raw_material.raw_material_mutation_export_excel, name="raw_material_mutation_export_excel"),
    path("raw-materials/mutations/new/", views_raw_material.raw_material_mutation_create, name="raw_material_mutation_create"),
    path("raw-materials/mutations/<uuid:uuid>/", views_raw_material.raw_material_mutation_detail, name="raw_material_mutation_detail"),
    path("raw-materials/mutations/<uuid:uuid>/update/", views_raw_material.raw_material_mutation_update, name="raw_material_mutation_update"),
    path("raw-materials/mutations/<uuid:uuid>/delete/", views_raw_material.raw_material_mutation_delete, name="raw_material_mutation_delete"),
    path("raw-materials/cards/", views_raw_material.raw_material_stock_card_index, name="raw_material_stock_card_index"),
    path("raw-materials/cards/export/", views_raw_material.raw_material_stock_card_export_excel, name="raw_material_stock_card_export_excel"),
    path("raw-materials/<uuid:uuid>/card/", views_raw_material.raw_material_stock_card, name="raw_material_stock_card"),

    # Realisasi Project Bertahap
    path("projects/realizations/", views_realization.project_realization_list, name="project_realization_list"),
    path("projects/realizations/export/", views_realization.project_realization_export_excel, name="project_realization_export_excel"),
    path("projects/<uuid:uuid>/realization/", views_realization.project_realization_detail, name="project_realization_detail"),
    path("projects/<uuid:project_uuid>/realization/bom/add/", views_realization.realization_bom_add, name="realization_bom_add"),
    path("realization/bom/<uuid:uuid>/delete/", views_realization.realization_bom_delete, name="realization_bom_delete"),
    path("projects/<uuid:project_uuid>/realization/labor/add/", views_realization.realization_labor_add, name="realization_labor_add"),
    path("realization/labor/<uuid:uuid>/delete/", views_realization.realization_labor_delete, name="realization_labor_delete"),
    path("projects/<uuid:project_uuid>/realization/fg/add/", views_realization.realization_fg_add, name="realization_fg_add"),
    path("realization/fg/<uuid:uuid>/delete/", views_realization.realization_fg_delete, name="realization_fg_delete"),
    path("projects/<uuid:project_uuid>/realization/overhead/add/", views_realization.realization_overhead_add, name="realization_overhead_add"),
    path("realization/overhead/<uuid:uuid>/delete/", views_realization.realization_overhead_delete, name="realization_overhead_delete"),

    # BOM
    path("projects/<uuid:project_uuid>/bom/add/", views.bom_item_add, name="bom_item_add"),
    path("bom/<uuid:uuid>/update/", views.bom_item_update, name="bom_item_update"),
    path("bom/<uuid:uuid>/delete/", views.bom_item_delete, name="bom_item_delete"),
    
    # Labor
    path("projects/<uuid:project_uuid>/labor/add/", views.labor_add, name="labor_add"),
    path("labor/<uuid:uuid>/update/", views.labor_update, name="labor_update"),
    path("labor/<uuid:uuid>/delete/", views.labor_delete, name="labor_delete"),
    
    # Overhead
    path("projects/<uuid:project_uuid>/overhead/add/", views.overhead_add, name="overhead_add"),
    path("overhead/<uuid:uuid>/update/", views.overhead_update, name="overhead_update"),
    path("overhead/<uuid:uuid>/delete/", views.overhead_delete, name="overhead_delete"),

    # Project Finished Goods (Barang Jadi di Project)
    path("projects/<uuid:project_uuid>/fg/add/", views.project_fg_add, name="project_fg_add"),
    path("project-fg/<uuid:uuid>/update/", views.project_fg_update, name="project_fg_update"),
    path("project-fg/<uuid:uuid>/delete/", views.project_fg_delete, name="project_fg_delete"),

    # Stock Management & Kartu Stock (Barang Jadi)
    path("finished-goods/", views_finished_good.finished_good_list, name="finished_good_list"),
    path("finished-goods/export/", views_finished_good.finished_good_export_excel, name="finished_good_export_excel"),
    path("finished-goods/new/", views_finished_good.finished_good_create, name="finished_good_create"),
    path("finished-goods/<uuid:uuid>/update/", views_finished_good.finished_good_update, name="finished_good_update"),
    path("finished-goods/<uuid:uuid>/delete/", views_finished_good.finished_good_delete, name="finished_good_delete"),
    path("finished-goods/mutations/", views_finished_good.finished_good_mutation_list, name="finished_good_mutation_list"),
    path("finished-goods/mutations/export/", views_finished_good.finished_good_mutation_export_excel, name="finished_good_mutation_export_excel"),
    path("finished-goods/mutations/new/", views_finished_good.finished_good_mutation_create, name="finished_good_mutation_create"),
    path("finished-goods/cards/", views_finished_good.finished_good_stock_card_index, name="finished_good_stock_card_index"),
    path("finished-goods/cards/export/", views_finished_good.finished_good_stock_card_export_excel, name="finished_good_stock_card_export_excel"),
    path("finished-goods/<uuid:uuid>/card/", views_finished_good.finished_good_stock_card, name="finished_good_stock_card"),
    
    # Backward compatibility aliases
    path("stock/", views_finished_good.finished_good_list, name="stock_report"),
    path("stock/new/", views_finished_good.finished_good_create, name="stock_create_legacy"),
    path("stock/add/", views_finished_good.finished_good_create, name="finished_good_form_view"),
    path("stock/mutations/", views_finished_good.finished_good_mutation_list, name="stock_mutation_list"),
    path("stock/mutations/export/", views_finished_good.finished_good_mutation_export_excel, name="stock_mutation_export_excel"),
    path("stock/mutations/new/", views_finished_good.finished_good_mutation_create, name="stock_mutation_general_create"),
    path("stock/cards/", views_finished_good.finished_good_stock_card_index, name="stock_card_index"),
    path("stock/cards/export/", views_finished_good.finished_good_stock_card_export_excel, name="stock_card_export_excel"),
    path("stock/<uuid:uuid>/update/", views_finished_good.finished_good_update, name="stock_update_legacy"),
    path("stock/<uuid:uuid>/delete/", views_finished_good.finished_good_delete, name="stock_delete_legacy"),
    path("stock/<uuid:uuid>/card/", views_finished_good.finished_good_stock_card, name="stock_card"),
    path("stock/<uuid:uuid>/mutation/", views.stock_mutation_create, name="stock_mutation_create"),
    
    # Export & Print
    path("projects/<uuid:uuid>/export/excel/", views.export_project_excel, name="export_project_excel"),
    path("projects/<uuid:uuid>/print/", views.print_project_pdf, name="print_project_pdf"),
    
    # Absensi & Karyawan
    path("attendance/", views.attendance_list, name="attendance_list"),
    path("attendance/new/", views.attendance_create, name="attendance_create"),
    path("attendance/<uuid:uuid>/update/", views.attendance_update, name="attendance_update"),
    path("attendance/<uuid:uuid>/delete/", views.attendance_delete, name="attendance_delete"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/new/", views.employee_create, name="employee_create"),
    path("employees/<uuid:uuid>/update/", views.employee_update, name="employee_update"),
    path("employees/<uuid:uuid>/delete/", views.employee_delete, name="employee_delete"),
    
    # Log Kinerja Karyawan
    path("work-logs/", views.work_log_list, name="work_log_list"),
    path("work-logs/new/", views.work_log_create, name="work_log_create"),
    path("work-logs/<uuid:uuid>/update/", views.work_log_update, name="work_log_update"),
    path("work-logs/<uuid:uuid>/delete/", views.work_log_delete, name="work_log_delete"),

    # Master Data Jenis Tidak Masuk (Absence Types)
    path("absence-types/", views_absence_type.absence_type_list, name="absence_type_list"),
    path("absence-types/new/", views_absence_type.absence_type_create, name="absence_type_create"),
    path("absence-types/<uuid:uuid>/update/", views_absence_type.absence_type_update, name="absence_type_update"),
    path("absence-types/<uuid:uuid>/delete/", views_absence_type.absence_type_delete, name="absence_type_delete"),
]
