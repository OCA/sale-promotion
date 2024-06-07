# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestSaleCouponRewardFixedPriceOrderLineLink(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("product.product_product_25_product_template")
        cls.partner = cls.env.ref("base.res_partner_3")
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [(0, 0, {"product_id": cls.product.id})],
            }
        )

        cls.coupon = cls.env["coupon.program"].create(
            {
                "name": "10%",
                "promo_code_usage": "no_code_needed",
                "reward_type": "fixed_price",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "discount_apply_on": "cheapest_product",
            }
        )

    def test_program_reward_fixed_price_specific_product(self):
        """
        Test that when adding a coupon of reward type "discount_line"
        the coupon program is correctly tracked on the SOL
        """
        self.assertFalse(self.order.order_line.coupon_program_id)
        self.order.recompute_coupon_lines()
        self.assertTrue(self.order.order_line.coupon_program_id)
