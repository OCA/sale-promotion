from odoo.tests import TransactionCase, tagged


@tagged("sale_loyalty_order_count_condition", "post_install", "-at_install")
class TestOrderCountCondition(TransactionCase):
    """A loyalty rule can require the customer's first order, the first order
    using its code, or a repeat order — counted on confirmed sale orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Haircut", "lst_price": 50.0}
        )
        cls.program = cls._create_program()

    @classmethod
    def _create_program(cls, condition=False, code="FIRST10"):
        return cls.env["loyalty.program"].create(
            {
                "name": "Conditional Promo",
                "program_type": "promo_code",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "with_code",
                            "code": code,
                            "customer_order_condition": condition,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "per_order",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

    @classmethod
    def _create_order(cls, partner=None):
        return cls.env["sale.order"].create(
            {
                "partner_id": (partner or cls.customer).id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "price_unit": 50.0})
                ],
            }
        )

    @classmethod
    def _apply_code(cls, order, code="FIRST10"):
        """Apply a promo code the way the eCommerce flow does: enable it, then
        claim the single reward."""
        status = order._try_apply_code(code)
        if "error" not in status and len(status) == 1:
            coupon, rewards = next(iter(status.items()))
            if len(rewards) == 1:
                order._apply_program_reward(rewards, coupon)
        return status

    def test_first_use_applies_once_per_customer(self):
        """A code conditioned on first use discounts the customer's first order
        but is refused on their next one."""
        self.program.rule_ids.customer_order_condition = "first_use"
        first = self._create_order()
        status = self._apply_code(first)
        self.assertNotIn("error", status)
        self.assertTrue(first.order_line.filtered("is_reward_line"))
        first.state = "sale"

        second = self._create_order()
        status = self._apply_code(second)
        self.assertIn("error", status)
        self.assertFalse(second.order_line.filtered("is_reward_line"))

    def test_first_ever_counts_any_prior_order(self):
        """A first-order condition is refused once the customer has any
        confirmed order, even one that did not use the code."""
        self.program.rule_ids.customer_order_condition = "first_ever"
        first = self._create_order()
        first.state = "sale"  # an unrelated purchase
        order = self._create_order()
        status = self._apply_code(order)
        self.assertIn("error", status)
        self.assertFalse(order.order_line.filtered("is_reward_line"))

    def test_repeat_ever_requires_a_prior_order(self):
        """A repeat-order condition is refused to a new customer and applies
        once they have a confirmed order."""
        self.program.rule_ids.customer_order_condition = "repeat_ever"
        first = self._create_order()
        self.assertIn("error", self._apply_code(first))
        first.state = "sale"

        second = self._create_order()
        status = self._apply_code(second)
        self.assertNotIn("error", status)
        self.assertTrue(second.order_line.filtered("is_reward_line"))

    def test_unconditioned_rule_always_applies(self):
        """Rules without the condition behave as before."""
        order = self._create_order()
        status = self._apply_code(order)
        self.assertNotIn("error", status)
        self.assertTrue(order.order_line.filtered("is_reward_line"))
