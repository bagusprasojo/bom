import os
import sys
from decimal import Decimal
import django
from django.utils import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from hpp.models import (
    Customer, Project, BOMItem, ProjectLabor, ProjectOverhead, 
    ProjectFinishedGood, FinishedGood, BOMItemRealization, RawMaterial
)
from hpp import views, views_customer


def add_session_and_messages(request):
    setattr(request, "session", {})
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    request.user = AnonymousUser()
    return request


def cleanup_data():
    BOMItemRealization.objects.filter(project__code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).delete()
    BOMItem.objects.filter(project__code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).update(parent=None)
    BOMItem.objects.filter(project__code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).delete()
    ProjectLabor.objects.filter(project__code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).delete()
    ProjectOverhead.objects.filter(project__code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).delete()
    ProjectFinishedGood.objects.filter(project__code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).delete()
    Project.objects.filter(code__in=[
        "PRJ-CUST-01", "PRJ-CUST-02", "PRJ-DEL-SAFE", 
        "PRJ-DEL-PROG", "PRJ-DEL-REAL", "PRJ-SRC-BOM", "PRJ-TGT-BOM"
    ]).delete()
    RawMaterial.objects.filter(code="RM-TEST-DEL").delete()
    Customer.objects.filter(code="CUST-OP-001").delete()


def run_tests():
    factory = RequestFactory()
    print("=== STARTING OPERATIONAL WORKFLOW TEST (STEP 2) ===")

    cleanup_data()

    try:
        # Setup Master Data for Test
        customer = Customer.objects.create(
            code="CUST-OP-001",
            name="PT Test Operasional Customer",
            company_name="Test Company",
            phone="08123456789"
        )

        # ----------------------------------------------------
        # TEST 1: Customer List & Projects Preload
        # ----------------------------------------------------
        print("\n--- TEST 1: Customer List & Project History ---")
        p_cust1 = Project.objects.create(
            code="PRJ-CUST-01",
            name="Proyek Cust Alpha",
            customer=customer,
            customer_name=customer.name,
            status="in_progress",
            progress_percentage=50,
            contract_value=Decimal("50000000")
        )
        p_cust2 = Project.objects.create(
            code="PRJ-CUST-02",
            name="Proyek Cust Beta",
            customer=customer,
            customer_name=customer.name,
            status="completed",
            progress_percentage=100,
            contract_value=Decimal("75000000")
        )

        req_cust = factory.get("/customers/")
        add_session_and_messages(req_cust)
        resp_cust = views_customer.customer_list(req_cust)
        assert resp_cust.status_code == 200, f"Customer list returned {resp_cust.status_code}"
        html_content = resp_cust.content.decode("utf-8")
        assert ("PRJ-CUST-01" in html_content or "PRJ\\u002DCUST\\u002D01" in html_content), "Project 1 code should be rendered in customer modal data"
        assert ("PRJ-CUST-02" in html_content or "PRJ\\u002DCUST\\u002D02" in html_content), "Project 2 code should be rendered in customer modal data"
        assert "2 Project" in html_content, "Should render '2 Project' badge for customer"
        print(f"PASS: Customer '{customer.name}' rendered with 2 projects successfully in HTML & Alpine data.")

        # ----------------------------------------------------
        # TEST 2: Project Delete Safeguards
        # ----------------------------------------------------
        print("\n--- TEST 2: Project Delete Safeguards ---")
        # 2a: Draft without realization -> SUCCESS
        p_draft_safe = Project.objects.create(
            code="PRJ-DEL-SAFE",
            name="Draft Project Safe To Delete",
            customer=customer,
            status="draft"
        )
        req_del1 = factory.post(f"/projects/{p_draft_safe.uuid}/delete/")
        add_session_and_messages(req_del1)
        resp_del1 = views.project_delete(req_del1, uuid=p_draft_safe.uuid)
        assert resp_del1.status_code == 302, f"Expected redirect, got {resp_del1.status_code}"
        assert not Project.objects.filter(id=p_draft_safe.id).exists(), "Draft project should be deleted"
        print("PASS: Draft project without realization deleted successfully.")

        # 2b: In-Progress project -> REJECTED
        p_in_prog = Project.objects.create(
            code="PRJ-DEL-PROG",
            name="In Progress Project",
            customer=customer,
            status="in_progress"
        )
        req_del2 = factory.post(f"/projects/{p_in_prog.uuid}/delete/")
        add_session_and_messages(req_del2)
        resp_del2 = views.project_delete(req_del2, uuid=p_in_prog.uuid)
        assert resp_del2.status_code == 302
        assert Project.objects.filter(id=p_in_prog.id).exists(), "In-progress project must NOT be deleted"
        print("PASS: In-progress project deletion was safely rejected.")

        # 2c: Draft with realization -> REJECTED
        p_draft_with_real = Project.objects.create(
            code="PRJ-DEL-REAL",
            name="Draft Project With Realization",
            customer=customer,
            status="draft"
        )
        rm = RawMaterial.objects.create(
            code="RM-TEST-DEL",
            name="Bahan Uji Realisasi",
            category="Kayu",
            stock_unit="pcs",
            current_stock=Decimal("10"),
            last_purchase_price=Decimal("10000")
        )
        bom_item = BOMItem.objects.create(
            project=p_draft_with_real,
            name="Item BOM 1",
            item_type="material",
            est_qty=Decimal("5"),
            est_unit_cost=Decimal("10000"),
            raw_material=rm
        )
        BOMItemRealization.objects.create(
            project=p_draft_with_real,
            date=timezone.now().date(),
            bom_item=bom_item,
            raw_material=rm,
            qty=Decimal("2"),
            unit_cost=Decimal("10000")
        )
        assert p_draft_with_real.has_realizations, "Project should have has_realizations=True"

        req_del3 = factory.post(f"/projects/{p_draft_with_real.uuid}/delete/")
        add_session_and_messages(req_del3)
        resp_del3 = views.project_delete(req_del3, uuid=p_draft_with_real.uuid)
        assert resp_del3.status_code == 302
        assert Project.objects.filter(id=p_draft_with_real.id).exists(), "Draft project with realizations must NOT be deleted"
        print("PASS: Draft project with realization deletion was safely rejected.")

        # ----------------------------------------------------
        # TEST 3: Copy / Duplicate BOM from Another Project
        # ----------------------------------------------------
        print("\n--- TEST 3: Duplicate / Copy BOM from Another Project ---")
        source_project = Project.objects.create(
            code="PRJ-SRC-BOM",
            name="Meja Kantor Kayu Solid (Source)",
            customer=customer,
            status="completed"
        )
        # Tree BOM: Root Sub-Assembly -> 2 Children
        sub_assembly = BOMItem.objects.create(
            project=source_project,
            name="Sub-Assembly Rangka Meja",
            item_type="sub_assembly",
            unit="set",
            est_qty=Decimal("1"),
            est_unit_cost=Decimal("0")
        )
        child1 = BOMItem.objects.create(
            project=source_project,
            parent=sub_assembly,
            name="Papan Kayu Mahoni",
            item_type="material",
            unit="m3",
            est_qty=Decimal("0.5"),
            est_unit_cost=Decimal("2000000")
        )
        child2 = BOMItem.objects.create(
            project=source_project,
            parent=sub_assembly,
            name="Kaki Meja Besi Hollow",
            item_type="material",
            unit="batang",
            est_qty=Decimal("4"),
            est_unit_cost=Decimal("125000")
        )
        # Root material outside sub-assembly
        root_mat = BOMItem.objects.create(
            project=source_project,
            parent=None,
            name="Finishing Melamic Clear",
            item_type="material",
            unit="kaleng",
            est_qty=Decimal("2"),
            est_unit_cost=Decimal("75000")
        )

        # Labor & Overhead
        labor = ProjectLabor.objects.create(
            project=source_project,
            role_name="Tukang Kayu Utama",
            unit="hari",
            est_quantity=Decimal("3"),
            est_rate=Decimal("150000")
        )
        ovh = ProjectOverhead.objects.create(
            project=source_project,
            name="Listrik Pabrik & Konsumsi",
            est_cost=Decimal("200000")
        )

        # Target Project
        target_project = Project.objects.create(
            code="PRJ-TGT-BOM",
            name="Pesanan 2x Meja Kantor Mahoni",
            customer=customer,
            status="draft"
        )

        # Test copy with multiplier 2.0
        req_copy = factory.post(f"/projects/{target_project.uuid}/copy-bom/", {
            "source_project_uuid": str(source_project.uuid),
            "copy_bom": "on",
            "copy_labor": "on",
            "copy_overhead": "on",
            "copy_fg": "on",
            "multiplier": "2.0"
        })
        add_session_and_messages(req_copy)
        resp_copy = views.project_copy_bom(req_copy, uuid=target_project.uuid)
        assert resp_copy.status_code == 302, f"Expected 302 redirect, got {resp_copy.status_code}"

        # Verify Cloned BOM Items
        target_boms = list(target_project.bom_items.all().order_by("id"))
        assert len(target_boms) == 4, f"Expected 4 BOM items in target, got {len(target_boms)}"

        # Check Hierarchy
        cloned_sub = next(b for b in target_boms if b.name == "Sub-Assembly Rangka Meja")
        assert cloned_sub.parent is None, "Sub-assembly should be a root item"
        assert cloned_sub.est_qty == Decimal("2.0"), f"Expected qty 2.0 (1.0 * 2), got {cloned_sub.est_qty}"

        cloned_child1 = next(b for b in target_boms if b.name == "Papan Kayu Mahoni")
        assert cloned_child1.parent_id == cloned_sub.id, f"Child 1 parent should be cloned sub-assembly id {cloned_sub.id}, got {cloned_child1.parent_id}"
        assert cloned_child1.est_qty == Decimal("1.0"), f"Expected qty 1.0 (0.5 * 2), got {cloned_child1.est_qty}"
        assert cloned_child1.est_unit_cost == Decimal("2000000")

        cloned_child2 = next(b for b in target_boms if b.name == "Kaki Meja Besi Hollow")
        assert cloned_child2.parent_id == cloned_sub.id, f"Child 2 parent should be cloned sub-assembly id {cloned_sub.id}"
        assert cloned_child2.est_qty == Decimal("8.0"), f"Expected qty 8.0 (4 * 2), got {cloned_child2.est_qty}"

        cloned_root = next(b for b in target_boms if b.name == "Finishing Melamic Clear")
        assert cloned_root.parent is None
        assert cloned_root.est_qty == Decimal("4.0"), f"Expected qty 4.0 (2 * 2), got {cloned_root.est_qty}"

        # Check Cloned Labor
        target_labors = list(target_project.labor_items.all())
        assert len(target_labors) == 1, f"Expected 1 labor item, got {len(target_labors)}"
        assert target_labors[0].est_quantity == Decimal("6.0"), f"Expected 6.0 days labor, got {target_labors[0].est_quantity}"
        assert target_labors[0].est_rate == Decimal("150000")

        # Check Cloned Overhead
        target_ovhs = list(target_project.overhead_items.all())
        assert len(target_ovhs) == 1, f"Expected 1 overhead item, got {len(target_ovhs)}"
        assert target_ovhs[0].est_cost == Decimal("400000"), f"Expected 400000 overhead, got {target_ovhs[0].est_cost}"

        print(f"PASS: Full BOM Hierarchy cloned with perfect parent-child integrity and 2.0x multiplier.")
        print(f"PASS: Labor and Overhead cloned accurately.")

        print("\n=== ALL STEP 2 AUTOMATED OPERATIONAL TESTS PASSED! ===")

    finally:
        cleanup_data()


if __name__ == "__main__":
    run_tests()
