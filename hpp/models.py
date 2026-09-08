from django.db import models, transaction
from django.apps import apps
from decimal import Decimal
import uuid



class RawMaterial(models.Model):
    """
    Master Data Bahan Baku (Raw Material)
    Stock dikelola dalam satuan dasar (stock_unit).
    Valuasi keuangan stok menggunakan harga beli terakhir (last_purchase_price).
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=100, blank=True, default="Umum")
    stock_unit = models.CharField(max_length=50, default="pcs")  # Satuan dasar persediaan
    current_stock = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Harga beli terakhir per stock_unit
    minimum_stock = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def total_inventory_value(self):
        return self.current_stock * self.last_purchase_price

    def __str__(self):
        return f"[{self.code}] {self.name} (Stock: {self.current_stock} {self.stock_unit})"


class RawMaterialUnitConversion(models.Model):
    """
    Multi-Satuan & Rasio Konversi Bahan Baku
    Contoh: 1 DUS = 100 PCS (conversion_factor = 100)
    1 LEMBAR = 2.88 M2 (conversion_factor = 2.88)
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name="conversions")
    unit_name = models.CharField(max_length=50)  # Satuan alternatif
    conversion_factor = models.DecimalField(max_digits=12, decimal_places=4, default=1)  # 1 unit_name = conversion_factor stock_unit
    notes = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        unique_together = ("raw_material", "unit_name")
        ordering = ["unit_name"]

    def __str__(self):
        return f"1 {self.unit_name} = {self.conversion_factor} {self.raw_material.stock_unit}"


class RawMaterialStockMutation(models.Model):
    """
    Kartu Stok & Riwayat Mutasi Bahan Baku (In / Out)
    """
    MUTATION_TYPES = [
        ("IN", "Stock Masuk (In)"),
        ("OUT", "Stock Keluar (Out)"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name="mutations")
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name="material_mutations")
    mutation_type = models.CharField(max_length=5, choices=MUTATION_TYPES)
    
    input_qty = models.DecimalField(max_digits=15, decimal_places=4)  # Jumlah satuan input
    input_unit = models.CharField(max_length=50)  # Satuan input
    stock_qty = models.DecimalField(max_digits=15, decimal_places=4)  # Jumlah dalam satuan dasar
    
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Harga per input_unit saat transaksi
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=15, decimal_places=4)  # Sisa stok dasar
    
    reference_no = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mutation_type} {self.input_qty} {self.input_unit} ({self.stock_qty} {self.raw_material.stock_unit}) - {self.raw_material.name}"

class MaterialMaster(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    name = models.CharField(max_length=200, unique=True)
    unit = models.CharField(max_length=50, default="pcs")
    standard_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.unit})"


class LaborMaster(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    role_name = models.CharField(max_length=200, unique=True)
    unit = models.CharField(max_length=50, default="jam")
    standard_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.role_name} ({self.unit})"


class FinishedGood(models.Model):
    """
    Master Barang Jadi (Stock Item)
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=100, blank=True, default="Umum")
    unit = models.CharField(max_length=50, default="unit")
    standard_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def total_inventory_value(self):
        return self.current_stock * self.standard_cost

    def __str__(self):
        return f"[{self.sku}] {self.name} (Stock: {self.current_stock} {self.unit})"


class Customer(models.Model):
    """
    Master Data Customer / Klien
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.company_name})" if self.company_name else self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft / Perencanaan"),
        ("in_progress", "Sedang Dikerjakan"),
        ("completed", "Selesai"),
        ("cancelled", "Dibatalkan"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=250)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    customer_name = models.CharField(max_length=200, blank=True, default="")
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    progress_percentage = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    stock_released = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    closing_notes = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.code}] {self.name}"

    @property
    def total_est_material(self):
        return sum(item.est_total for item in self.bom_items.filter(item_type="material"))

    @property
    def total_act_material(self):
        # Akumulasi dari log realisasi bertahap jika ada
        if self.bom_realizations.exists():
            return sum(r.total_cost for r in self.bom_realizations.all())
        return sum(item.act_total for item in self.bom_items.filter(item_type="material"))

    @property
    def total_est_labor(self):
        return sum(item.est_total for item in self.labor_items.all())

    @property
    def total_act_labor(self):
        # Akumulasi dari log realisasi bertahap jika ada
        if self.labor_realizations.exists():
            return sum(r.total_cost for r in self.labor_realizations.all())
        return sum(item.act_total for item in self.labor_items.all())

    @property
    def total_est_overhead(self):
        return sum(item.est_cost for item in self.overhead_items.all())

    @property
    def total_act_overhead(self):
        # Akumulasi dari log realisasi bertahap jika ada
        if self.overhead_realizations.exists():
            return sum(r.cost for r in self.overhead_realizations.all())
        return sum(item.act_cost for item in self.overhead_items.all())

    @property
    def total_est_finished_goods(self):
        return sum(item.est_total for item in self.finished_good_items.all())

    @property
    def total_act_finished_goods(self):
        # Akumulasi dari log realisasi bertahap jika ada
        if self.finished_good_realizations.exists():
            return sum(r.total_cost for r in self.finished_good_realizations.all())
        return sum(item.act_total for item in self.finished_good_items.all())

    @property
    def total_hpp_estimated(self):
        return (
            self.total_est_material
            + self.total_est_labor
            + self.total_est_overhead
            + self.total_est_finished_goods
        )

    @property
    def total_hpp_actual(self):
        return (
            self.total_act_material
            + self.total_act_labor
            + self.total_act_overhead
            + self.total_act_finished_goods
        )

    @property
    def est_gross_profit(self):
        return self.contract_value - self.total_hpp_estimated

    @property
    def act_gross_profit(self):
        return self.contract_value - self.total_hpp_actual

    @property
    def est_margin_pct(self):
        if self.contract_value > 0:
            return (self.est_gross_profit / self.contract_value) * Decimal(100)
        return Decimal(0)

    @property
    def act_margin_pct(self):
        if self.contract_value > 0:
            return (self.act_gross_profit / self.contract_value) * Decimal(100)
        return Decimal(0)

    @property
    def has_realizations(self):
        """
        Mengecek apakah proyek sudah memiliki pencatatan transaksi riil / mutasi persediaan.
        """
        return (
            self.bom_realizations.exists() or
            self.labor_realizations.exists() or
            self.finished_good_realizations.exists() or
            self.overhead_realizations.exists() or
            self.stock_mutations.exists()
        )

    def release_stock_if_completed(self, fg=None, qty=0, notes=""):
        """
        Jika closing proyek menghasilkan barang jadi untuk disimpan ke gudang persediaan,
        tambahkan kuantitas ke FinishedGood.current_stock dan catat FinishedGoodStockMutation bertipe 'IN'.
        """
        if self.status != "completed" or self.stock_released:
            return None
        
        if fg and Decimal(qty or 0) > 0:
            with transaction.atomic():
                fg.current_stock += Decimal(qty)
                fg.save(update_fields=["current_stock"])

                FinishedGoodStockMutation = apps.get_model("hpp", "FinishedGoodStockMutation")
                mutation = FinishedGoodStockMutation.objects.create(
                    finished_good=fg,
                    project=self,
                    mutation_type="IN",
                    quantity=Decimal(qty),
                    balance_after=fg.current_stock,
                    reference_no=f"PROD-{self.code}",
                    notes=f"Hasil produksi closing project {self.code} ({self.name}) - {notes}".strip()
                )
                self.stock_released = True
                self.save(update_fields=["stock_released"])
                return mutation
        return None

    def revert_stock_release(self):
        """
        Rollback penambahan stok barang jadi jika proyek yang sudah selesai dibuka kembali (Reopen).
        Menghitung selisih bersih (net unreverted) agar aman dari multiple close/reopen cycle.
        """
        with transaction.atomic():
            FinishedGoodStockMutation = apps.get_model("hpp", "FinishedGoodStockMutation")
            in_mutations = FinishedGoodStockMutation.objects.filter(
                project=self,
                reference_no__startswith=f"PROD-{self.code}",
                mutation_type="IN"
            )
            out_mutations = FinishedGoodStockMutation.objects.filter(
                project=self,
                reference_no__startswith=f"CANCEL-PROD-{self.code}",
                mutation_type="OUT"
            )

            total_by_fg = {}
            for m in in_mutations:
                total_by_fg[m.finished_good_id] = total_by_fg.get(m.finished_good_id, Decimal(0)) + m.quantity
            for m in out_mutations:
                total_by_fg[m.finished_good_id] = total_by_fg.get(m.finished_good_id, Decimal(0)) - m.quantity

            FinishedGood = apps.get_model("hpp", "FinishedGood")
            for fg_id, net_qty in total_by_fg.items():
                if net_qty > Decimal(0):
                    fg = FinishedGood.objects.get(id=fg_id)
                    fg.current_stock -= net_qty
                    fg.save(update_fields=["current_stock"])

                    FinishedGoodStockMutation.objects.create(
                        finished_good=fg,
                        project=self,
                        mutation_type="OUT",
                        quantity=net_qty,
                        balance_after=fg.current_stock,
                        reference_no=f"CANCEL-PROD-{self.code}",
                        notes=f"Rollback hasil produksi karena pembukaan kembali project {self.code}"
                    )
            
            self.stock_released = False
            self.save(update_fields=["stock_released"])


class BOMItem(models.Model):
    ITEM_TYPES = [
        ("assembly", "Sub-Assembly / Rakitan"),
        ("material", "Material / Bahan Mentah"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="bom_items")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default="material")
    material_master = models.ForeignKey(MaterialMaster, on_delete=models.SET_NULL, null=True, blank=True)
    raw_material = models.ForeignKey('RawMaterial', on_delete=models.SET_NULL, null=True, blank=True, related_name="bom_items")
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default="pcs")
    
    est_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    est_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    act_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    act_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = models.TextField(blank=True, default="")

    def save(self, *args, **kwargs):
        if self.item_type == "material":
            if not self.raw_material and self.name:
                rm = RawMaterial.objects.filter(name__iexact=self.name.strip()).first()
                if rm:
                    self.raw_material = rm
            if not self.material_master and self.name:
                master, _ = MaterialMaster.objects.get_or_create(
                    name=self.name.strip(),
                    defaults={"unit": self.unit or "pcs", "standard_cost": self.est_unit_cost or 0}
                )
                self.material_master = master
        super().save(*args, **kwargs)

    @property
    def est_total(self):
        if self.item_type == "assembly":
            return sum(child.est_total for child in self.children.all())
        return self.est_qty * self.est_unit_cost

    @property
    def total_realized_qty(self):
        return sum(r.qty for r in self.realizations.all())

    @property
    def total_realized_cost(self):
        return sum(r.total_cost for r in self.realizations.all())

    @property
    def act_total(self):
        if self.item_type == "assembly":
            return sum(child.act_total for child in self.children.all())
        if self.realizations.exists():
            return self.total_realized_cost
        return self.act_qty * self.act_unit_cost

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.name}"


class ProjectLabor(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="labor_items")
    labor_master = models.ForeignKey(LaborMaster, on_delete=models.SET_NULL, null=True, blank=True)
    role_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default="jam")

    est_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    est_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    act_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    act_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = models.TextField(blank=True, default="")

    def save(self, *args, **kwargs):
        if not self.labor_master and self.role_name:
            master, _ = LaborMaster.objects.get_or_create(
                role_name=self.role_name.strip(),
                defaults={"unit": self.unit or "jam", "standard_rate": self.est_rate or 0}
            )
            self.labor_master = master
        super().save(*args, **kwargs)

    @property
    def est_total(self):
        return self.est_quantity * self.est_rate

    @property
    def total_realized_quantity(self):
        return sum(r.quantity for r in self.realizations.all())

    @property
    def total_realized_cost(self):
        return sum(r.total_cost for r in self.realizations.all())

    @property
    def act_total(self):
        if self.realizations.exists():
            return self.total_realized_cost
        return self.act_quantity * self.act_rate


class ProjectOverhead(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="overhead_items")
    name = models.CharField(max_length=200)
    est_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    act_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")

    @property
    def total_realized_cost(self):
        return sum(r.cost for r in self.realizations.all())

    def __str__(self):
        return self.name


class ProjectFinishedGood(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="finished_good_items")
    finished_good = models.ForeignKey(FinishedGood, on_delete=models.PROTECT, related_name="project_usages")
    
    est_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    est_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    act_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    act_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = models.TextField(blank=True, default="")

    @property
    def est_total(self):
        return self.est_qty * self.est_unit_cost

    @property
    def total_realized_qty(self):
        return sum(r.quantity for r in self.realizations.all())

    @property
    def total_realized_cost(self):
        return sum(r.total_cost for r in self.realizations.all())

    @property
    def act_total(self):
        if self.realizations.exists():
            return self.total_realized_cost
        return self.act_qty * self.act_unit_cost

    def __str__(self):
        return f"{self.finished_good.name} for {self.project.code}"


class FinishedGoodStockMutation(models.Model):
    MUTATION_TYPES = [
        ("IN", "Stock Masuk (In)"),
        ("OUT", "Stock Keluar (Out)"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    finished_good = models.ForeignKey(FinishedGood, on_delete=models.CASCADE, related_name="mutations")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_mutations")
    mutation_type = models.CharField(max_length=5, choices=MUTATION_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference_no = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mutation_type} {self.quantity} {self.finished_good.unit} - {self.finished_good.name}"


# ==========================================
# MODEL REALISASI PROJECT BERTAHAP
# ==========================================

class BOMItemRealization(models.Model):
    """
    Realisasi pemakaian Material / Bahan Baku pada project.
    Jika terhubung dengan RawMaterial, langsung memotong stock dasar dan update harga beli terakhir.
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="bom_realizations")
    bom_item = models.ForeignKey(BOMItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="realizations")
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name="realizations")
    date = models.DateField()
    item_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default="pcs")
    qty = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_substitute = models.BooleanField(default=False)
    mutation = models.ForeignKey(RawMaterialStockMutation, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.total_cost = self.qty * self.unit_cost
            is_new = self.pk is None

            # Cek dan hubungkan ke RawMaterial jika ada nama yang cocok
            if not self.raw_material and self.item_name:
                rm = RawMaterial.objects.filter(name__iexact=self.item_name.strip()).first()
                if rm:
                    self.raw_material = rm

            if is_new and self.raw_material:
                rm = self.raw_material
                factor = Decimal(1)
                if self.unit.lower() != rm.stock_unit.lower():
                    conv = rm.conversions.filter(unit_name__iexact=self.unit.strip()).first()
                    if conv:
                        factor = conv.conversion_factor

                base_qty = self.qty * factor
                rm.current_stock -= base_qty

                # CATATAN: last_purchase_price tidak diubah pada saat pemakaian project (OUT).
                # last_purchase_price hanya mencerminkan harga beli aktual dari supplier pada transaksi masuk (IN).

                rm.save()

                mut = RawMaterialStockMutation.objects.create(
                    raw_material=rm,
                    project=self.project,
                    mutation_type="OUT",
                    input_qty=self.qty,
                    input_unit=self.unit,
                    stock_qty=base_qty,
                    unit_price=self.unit_cost,
                    total_price=self.total_cost,
                    balance_after=rm.current_stock,
                    reference_no=f"REAL-{self.project.code}",
                    notes=f"Realisasi material project {self.project.code} ({self.project.name}) - {self.notes}".strip()
                )
                self.mutation = mut

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self.raw_material and self.mutation:
                rm = self.raw_material
                factor = Decimal(1)
                if self.unit.lower() != rm.stock_unit.lower():
                    conv = rm.conversions.filter(unit_name__iexact=self.unit.strip()).first()
                    if conv:
                        factor = conv.conversion_factor

                base_qty = self.qty * factor
                rm.current_stock += base_qty
                rm.save()

                RawMaterialStockMutation.objects.create(
                    raw_material=rm,
                    project=self.project,
                    mutation_type="IN",
                    input_qty=self.qty,
                    input_unit=self.unit,
                    stock_qty=base_qty,
                    unit_price=self.unit_cost,
                    total_price=self.total_cost,
                    balance_after=rm.current_stock,
                    reference_no=f"CANCEL-REAL-{self.project.code}",
                    notes=f"Pembatalan realisasi material project {self.project.code}"
                )
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.item_name} ({self.qty} {self.unit})"


class LaborRealization(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="labor_realizations")
    project_labor = models.ForeignKey(ProjectLabor, on_delete=models.SET_NULL, null=True, blank=True, related_name="realizations")
    date = models.DateField()
    role_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default="jam")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_additional = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.role_name} ({self.quantity} {self.unit})"


class FinishedGoodRealization(models.Model):
    """
    Realisasi pemakaian Barang Jadi pada project.
    Saat disimpan langsung memotong stock dan mencatat mutasi OUT.
    Saat dihapus mengembalikan stock dan mencatat mutasi IN koreksi.
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="finished_good_realizations")
    project_fg = models.ForeignKey(ProjectFinishedGood, on_delete=models.SET_NULL, null=True, blank=True, related_name="realizations")
    finished_good = models.ForeignKey(FinishedGood, on_delete=models.PROTECT, related_name="realizations")
    date = models.DateField()
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mutation = models.ForeignKey(FinishedGoodStockMutation, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.total_cost = self.quantity * self.unit_cost
            is_new = self.pk is None
            
            if is_new:
                # Potong stok langsung
                fg = self.finished_good
                fg.current_stock -= self.quantity
                fg.save(update_fields=["current_stock"])

                mut = FinishedGoodStockMutation.objects.create(
                    finished_good=fg,
                    project=self.project,
                    mutation_type="OUT",
                    quantity=self.quantity,
                    balance_after=fg.current_stock,
                    reference_no=f"REAL-{self.project.code}",
                    notes=f"Realisasi project {self.project.code} ({self.project.name}) - {self.notes}".strip()
                )
                self.mutation = mut
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # Rollback stok
            fg = self.finished_good
            fg.current_stock += self.quantity
            fg.save(update_fields=["current_stock"])

            FinishedGoodStockMutation.objects.create(
                finished_good=fg,
                project=self.project,
                mutation_type="IN",
                quantity=self.quantity,
                balance_after=fg.current_stock,
                reference_no=f"CANCEL-REAL-{self.project.code}",
                notes=f"Pembatalan log realisasi project {self.project.code}"
            )
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.finished_good.name} ({self.quantity} {self.finished_good.unit})"


class OverheadRealization(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="overhead_realizations")
    project_overhead = models.ForeignKey(ProjectOverhead, on_delete=models.SET_NULL, null=True, blank=True, related_name="realizations")
    date = models.DateField()
    expense_name = models.CharField(max_length=200)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_additional = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} - {self.expense_name} (Cost: {self.cost})"


# ==========================================
# MODEL SDM, ABSENSI & KINERJA
# ==========================================

class Employee(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    nik = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=100, default="Tukang")
    daily_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overtime_rate_per_hour = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"[{self.nik}] {self.name} ({self.position})"


class AbsenceType(models.Model):
    """
    Master Data Jenis Tidak Masuk Karyawan (Cuti, Izin, Sakit, Dinas Luar, Alpha)
    Mendukung konfigurasi persentase pemotongan/pemberian upah (paid/unpaid leave).
    """
    CATEGORY_CHOICES = [
        ("LEAVE", "Cuti (Leave)"),
        ("SICK", "Sakit (Sick)"),
        ("PERMIT", "Izin (Permit)"),
        ("OFFICIAL_TRAVEL", "Dinas Luar / Tugas Lapangan"),
        ("ABSENT", "Alpha / Tanpa Keterangan"),
        ("OTHER", "Lain-lain"),
    ]

    COLOR_CHOICES = [
        ("blue", "Biru (Izin/Permit)"),
        ("amber", "Kuning/Oranye (Sakit)"),
        ("purple", "Ungu (Cuti/Leave)"),
        ("indigo", "Indigo (Dinas Luar)"),
        ("rose", "Merah (Alpha/Mangkir)"),
        ("slate", "Abu-abu (Lainnya)"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="PERMIT")
    is_paid = models.BooleanField(default=False, help_text="Apakah karyawan tetap berhak atas upah harian?")
    wage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="% upah harian yang dibayarkan (100 = penuh, 50 = separuh, 0 = unpaid)")
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="blue")
    requires_attachment = models.BooleanField(default=False, help_text="Wajib melampirkan surat/bukti?")
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        paid_label = f"Dibayar {self.wage_percentage:g}%" if self.is_paid else "Tanpa Upah"
        return f"[{self.code}] {self.name} ({paid_label})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("HADIR", "Hadir / Masuk"),
        ("TIDAK_HADIR", "Tidak Masuk (Izin/Cuti/Sakit)"),
        ("IJIN", "Izin (Legacy)"),
        ("SAKIT", "Sakit (Legacy)"),
        ("ALPHA", "Alpha (Legacy)"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    absence_type = models.ForeignKey(AbsenceType, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendances")
    date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="HADIR")
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    wage = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__name"]
        unique_together = ("employee", "date")

    @property
    def display_status_label(self):
        if self.status == "HADIR":
            return "Hadir / Masuk"
        if self.absence_type:
            return self.absence_type.name
        return self.get_status_display()

    @property
    def badge_color(self):
        if self.status == "HADIR":
            return "emerald"
        if self.absence_type:
            return self.absence_type.color
        if self.status == "IJIN":
            return "blue"
        if self.status == "SAKIT":
            return "amber"
        return "rose"

    def save(self, *args, **kwargs):
        if self.status == "HADIR":
            base_wage = self.employee.daily_rate
            ot_wage = self.overtime_hours * self.employee.overtime_rate_per_hour
            self.wage = base_wage + ot_wage
        elif self.absence_type:
            pct = (self.absence_type.wage_percentage or Decimal(0)) / Decimal(100)
            self.wage = self.employee.daily_rate * pct
        else:
            self.wage = Decimal(0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.employee.name} ({self.display_status_label})"


class EmployeeWorkLog(models.Model):
    STATUS_CHOICES = [
        ("completed", "Selesai"),
        ("in_progress", "Sedang Berjalan"),
        ("pending", "Tertunda / Terkendala"),
    ]

    RATING_CHOICES = [
        (5, "5 - Sangat Baik"),
        (4, "4 - Baik"),
        (3, "3 - Cukup"),
        (2, "2 - Kurang"),
        (1, "1 - Sangat Kurang"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="work_logs")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_work_logs")
    date = models.DateField()
    activity_category = models.CharField(max_length=100, default="Produksi / Fabrikasi")
    task_description = models.TextField()
    output_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    output_unit = models.CharField(max_length=50, default="unit")
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    obstacles = models.TextField(blank=True, default="")
    supervisor_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} - {self.employee.name}: {self.task_description[:30]}"


class UnitMaster(models.Model):
    CATEGORY_CHOICES = [
        ("raw_material", "Bahan Baku"),
        ("finished_good", "Barang Jadi"),
        ("labor", "Tenaga Kerja"),
        ("overhead", "Overhead / Biaya Lain"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="raw_material", db_index=True)
    description = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        unique_together = ("code", "category")

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.get_category_display()}"
