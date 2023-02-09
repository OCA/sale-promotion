# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, SavepointCase


class SaleCouponApplyCommercialPartnerCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commercial_entity = cls.env["res.partner"].create({"name": "Mrs. Odoo"})
        cls.child_1 = cls.commercial_entity.copy(
            {"name": "Baby Odoo", "parent_id": cls.commercial_entity.id}
        )
        cls.child_2 = cls.child_1.copy({"name": "Odoo Jr."})
        cls.other_partner = cls.commercial_entity.copy({"name": "Mr. OCA"})
        coupon_program_form = Form(
            cls.env["sale.coupon.program"],
            view="sale_coupon.sale_coupon_program_view_form",
        )
        coupon_program_form.name = "Test Apply Commercial Entity"
        cls.code_promotion_program = coupon_program_form.save()
        cls.env["sale.coupon.generate"].with_context(
            active_id=cls.code_promotion_program.id
        ).create(
            {
                "generation_type": "nbr_customer",
                "partners_domain": f"[('id', 'in', [{cls.child_1.id}])]",
            }
        ).generate_coupon()
        cls.coupon = cls.code_promotion_program.coupon_ids
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test 1", "sale_ok": True, "list_price": 50}
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.child_2
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()


class TestSaleCouponApplyCommercialPartner(SaleCouponApplyCommercialPartnerCase):
    def test_sale_coupon_apply_commercial_partner(self):
        self.assertEqual(self.coupon.state, "new")
        msg = self.coupon._check_coupon_code(self.sale)
        # We can use the coupon with other partner of the entity
        self.assertFalse(msg.get("error"))
        self.coupon.partner_id = self.other_partner
        # The expected behavior with other partners
        msg = self.coupon._check_coupon_code(self.sale)
        self.assertTrue(bool(msg.get("error")))
