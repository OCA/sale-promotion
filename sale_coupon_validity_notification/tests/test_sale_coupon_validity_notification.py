# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class TestSaleCouponValidity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.coupon_program = cls._create_coupon_program(cls)
        # Create a sale order that generates a coupon
        cls.order_a = cls._create_sale_order(cls)
        cls.order_a.recompute_coupon_lines()
        cls.order_a.action_confirm()
        cls.generated_coupon = cls.order_a.generated_coupon_ids
        # Create a sale order and apply the coupon
        cls.order_b = cls._create_sale_order(cls)
        cls.env["sale.coupon.apply.code"].with_context(active_id=cls.order_b.id).create(
            {"coupon_code": cls.generated_coupon.code}
        ).process_coupon()

    def _create_coupon_program(self):
        coupon_program_form = Form(
            self.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test coupon program"
        coupon_program_form.rule_products_domain = [("id", "=", self.product.id)]
        coupon_program_form.rule_min_quantity = 3
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.promo_applicability = "on_next_order"
        coupon_program_form.discount_type = "fixed_amount"
        coupon_program_form.discount_fixed_amount = 10
        return coupon_program_form.save()

    def _create_sale_order(self):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 5
            line_form.price_unit = 100
        return sale_form.save()

    def test_sale_coupon_validity_notification(self):
        messages = len(self.order_b.message_ids)
        activities = len(self.order_b.activity_ids)
        self.order_a.action_cancel()
        self.assertTrue(len(self.order_b.message_ids), messages + 1)
        self.assertTrue(
            self.order_b.message_ids.filtered(lambda msg: "has expired" in msg.body)
        )
        self.assertTrue(len(self.order_b.activity_ids), activities + 1)
        self.assertTrue(
            self.order_b.activity_ids.filtered(lambda act: "has expired" in act.note)
        )
