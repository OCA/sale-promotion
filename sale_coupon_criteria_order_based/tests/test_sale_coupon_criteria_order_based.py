# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


class TestSaleCouponCriteriaOrderBased(TestSaleCouponCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_program_rules_order_based(self):
        """
        Check program rules based on order domain
        """
        partner_test = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test@example.com",
            }
        )
        user_test = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": "test",
                    "password": "test",
                    "partner_id": partner_test.id,
                    "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
                }
            )
        )
        # Update program order domain. The program should be applied for order
        # if Salesperson of the order is 'Test' user
        self.immediate_promotion_program.write(
            {"rule_order_domain": "[('user_id.id', '=', %s)]" % (user_test.id)}
        )
        order = self.empty_order
        order.write(
            {
                "order_line": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_A.id,
                            "name": "1 Product A",
                            "product_uom": self.uom_unit.id,
                            "product_uom_qty": 1.0,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_B.id,
                            "name": "2 Product B",
                            "product_uom": self.uom_unit.id,
                            "product_uom_qty": 1.0,
                        },
                    ),
                ]
            }
        )
        order.recompute_coupon_lines()
        self.assertEqual(
            len(order.order_line.ids),
            2,
            "The promo offer shouldn't have been applied.",
        )
        order.user_id = user_test.id
        order.recompute_coupon_lines()
        self.assertEqual(
            len(order.order_line.ids),
            3,
            "The promo offer should have been applied.",
        )
