from django.contrib import admin
from .models import Project, MaterialMaster, LaborMaster, FinishedGood, BOMItem, ProjectLabor, ProjectOverhead, ProjectFinishedGood, FinishedGoodStockMutation

@admin.register(MaterialMaster)
class MaterialMasterAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "unit", "standard_cost")
    search_fields = ("name", "code")

@admin.register(LaborMaster)
class LaborMasterAdmin(admin.ModelAdmin):
    list_display = ("role_name", "unit", "standard_rate")
    search_fields = ("role_name",)

@admin.register(FinishedGood)
class FinishedGoodAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "unit", "standard_cost", "current_stock")
    search_fields = ("sku", "name")

class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 0

class ProjectLaborInline(admin.TabularInline):
    model = ProjectLabor
    extra = 0

class ProjectOverheadInline(admin.TabularInline):
    model = ProjectOverhead
    extra = 0

class ProjectFinishedGoodInline(admin.TabularInline):
    model = ProjectFinishedGood
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "customer_name", "status", "stock_released", "progress_percentage", "contract_value", "total_hpp_estimated", "total_hpp_actual")
    list_filter = ("status", "stock_released")
    search_fields = ("code", "name", "customer_name")
    inlines = [BOMItemInline, ProjectLaborInline, ProjectFinishedGoodInline, ProjectOverheadInline]

@admin.register(FinishedGoodStockMutation)
class FinishedGoodStockMutationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "finished_good", "mutation_type", "quantity", "balance_after", "reference_no", "project")
    list_filter = ("mutation_type",)
    search_fields = ("finished_good__name", "reference_no")
