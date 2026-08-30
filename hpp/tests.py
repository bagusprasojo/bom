from django.test import TestCase
from decimal import Decimal
from .models import Project, BOMItem, ProjectLabor, ProjectOverhead, MaterialMaster, LaborMaster


class HPPCalculationTest(TestCase):
    def test_hpp_and_master_sync(self):
        project = Project.objects.create(
            code="PRJ-TEST-01",
            name="Pembuatan Rak Besi",
            contract_value=Decimal("10000000"),
            status="in_progress",
            progress_percentage=50
        )
        self.assertIsNotNone(project.uuid)

        bom_mat = BOMItem.objects.create(
            project=project,
            name="Besi Hollow 4x4",
            unit="batang",
            est_qty=Decimal("10"),
            est_unit_cost=Decimal("150000"),
            act_qty=Decimal("12"),
            act_unit_cost=Decimal("155000")
        )
        self.assertIsNotNone(bom_mat.uuid)
        self.assertTrue(MaterialMaster.objects.filter(name="Besi Hollow 4x4").exists())
        self.assertEqual(bom_mat.est_total, Decimal("1500000"))
        self.assertEqual(bom_mat.act_total, Decimal("1860000"))

        labor = ProjectLabor.objects.create(
            project=project,
            role_name="Tukang Las",
            unit="hari",
            est_quantity=Decimal("5"),
            est_rate=Decimal("200000"),
            act_quantity=Decimal("6"),
            act_rate=Decimal("200000")
        )
        self.assertIsNotNone(labor.uuid)
        self.assertTrue(LaborMaster.objects.filter(role_name="Tukang Las").exists())

        overhead = ProjectOverhead.objects.create(
            project=project,
            name="Ongkir Truk",
            est_cost=Decimal("300000"),
            act_cost=Decimal("350000")
        )
        self.assertIsNotNone(overhead.uuid)

        self.assertEqual(project.total_hpp_estimated, Decimal("2800000"))
        self.assertEqual(project.total_hpp_actual, Decimal("3410000"))
        self.assertEqual(project.act_gross_profit, Decimal("10000000") - Decimal("3410000"))

        # Test view access with uuid
        response = self.client.get(f"/projects/{project.uuid}/")
        self.assertEqual(response.status_code, 200)
