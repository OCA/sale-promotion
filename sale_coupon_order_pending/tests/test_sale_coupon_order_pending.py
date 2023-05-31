# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class TestSaleCouponOrderPending(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.other_partner = cls.partner.copy({"name": "Mr. OCA"})
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Pending Coupons"
        cls.code_promotion_program = coupon_program_form.save()
        cls.env["coupon.generate.wizard"].with_context(
            active_id=cls.code_promotion_program.id
        ).create(
            {
                "generation_type": "nbr_customer",
                "partners_domain": (
                    f"[('id', 'in', {(cls.partner + cls.other_partner).ids})]"
                ),
            }
        ).generate_coupon()
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test 1", "sale_ok": True, "list_price": 50}
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()

    def test_coupon_order_pending(self):
        self.assertEqual(self.sale.pending_partner_coupon_count, 1)
        action = self.sale.action_view_pending_partner_coupons()
        pending_coupon = self.env["coupon.coupon"].search(action["domain"])
        pending_coupon = pending_coupon.with_context(**action["context"])
        # import wdb;wdb.set_trace()
        self.assertTrue(pending_coupon.can_be_applied_to_order)
        pending_coupon.action_apply_partner_coupon()
        self.assertEqual(self.sale.applied_coupon_ids, pending_coupon)
