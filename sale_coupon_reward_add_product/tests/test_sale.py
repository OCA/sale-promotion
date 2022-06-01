# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestCouponAddProduct(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.product = cls.env["product.product"].create({"name": "Test"})
        cls.program = cls.env["coupon.program"].create(
            {
                "name": "Test Free Product Auto",
                "promo_code_usage": "code_needed",
                "promo_code": "TEST_FREE_PRODUCT_AUTO",
                "reward_type": "product",
                "reward_product_id": cls.product.id,
                "reward_product_add_if_missing": True,
            }
        )
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def _apply_coupon(self, order, coupon_code):
        return self.env["sale.coupon.apply.code"].apply_coupon(order, coupon_code)

    def _generate_coupon(self, program):
        CouponGenerateWizard = self.env["coupon.generate.wizard"]
        wizard = CouponGenerateWizard.with_context(active_id=program.id).create({})
        wizard.generate_coupon()
        return program.coupon_ids[-1]

    def test_program_code_auto(self):
        res = self._apply_coupon(self.order, self.program.promo_code)
        self.assertFalse(res)
        self.assertEqual(len(self.order.order_line), 2)
        self.assertIn(self.program.reward_product_id, self.order.order_line.product_id)

    def test_coupon_code_auto(self):
        coupon = self._generate_coupon(self.program)
        res = self._apply_coupon(self.order, coupon.code)
        self.assertFalse(res)
        self.assertEqual(len(self.order.order_line), 2)
        self.assertIn(self.program.reward_product_id, self.order.order_line.product_id)

    def test_program_code_disabled(self):
        self.program.reward_product_add_if_missing = False
        res = self._apply_coupon(self.order, self.program.promo_code)
        self.assertEqual(
            res["error"],
            "The reward products should be in the sales order lines to apply the discount.",
        )
        self.assertFalse(self.order.order_line)

    def test_coupon_code_disabled(self):
        self.program.reward_product_add_if_missing = False
        coupon = self._generate_coupon(self.program)
        res = self._apply_coupon(self.order, coupon.code)
        self.assertEqual(
            res["error"],
            "The reward products should be in the sales order lines to apply the discount.",
        )
        self.assertFalse(self.order.order_line)
