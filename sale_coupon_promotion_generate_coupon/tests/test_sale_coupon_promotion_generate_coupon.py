# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.coupon_promotion_generate_coupon.tests import (
    test_coupon_promotion_generate_coupon,
)


class TestSaleCouponGenerateCoupon(
    test_coupon_promotion_generate_coupon.TestCouponGenerateCoupon
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()
        cls.sale.recompute_coupon_lines()

    def test_sale_coupon_promotion_generate_coupon(self):
        self.assertEqual(
            self.coupon_program.coupon_ids,
            self.sale.generated_coupon_ids,
            "A coupon should be generated in the coupon program and linked in the sale",
        )
        self.assertEqual(
            self.promotion_program,
            self.sale.no_code_promo_program_ids,
            "The coupon generator program should be linked to the sales order",
        )
        self.assertEqual(
            1,
            self.promotion_program.coupon_count,
            "The coupon counter should be updated in the coupon generator program",
        )
        self.sale.action_confirm()
        # Let's use the generate coupon, which can have a different rules set
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_1
            line_form.product_uom_qty = 2
        sale_2 = sale_form.save()
        apply_coupon = (
            self.env["sale.coupon.apply.code"]
            .with_context(active_id=sale_2.id)
            .create({"coupon_code": self.sale.generated_coupon_ids.code})
        )
        # The rules of the coupon program don't fit this sale order
        with self.assertRaises(UserError):
            apply_coupon.process_coupon()
        sale_2.order_line.product_id = self.product_2
        # Now we're talkin :)
        apply_coupon.process_coupon()
        self.assertEqual(
            sale_2.applied_coupon_ids,
            self.sale.generated_coupon_ids,
            "The applied coupon should be linked to the sales order",
        )
        self.assertEqual(
            1,
            self.promotion_program.order_count,
            "We should get the order count in the coupon generator promotion program",
        )
