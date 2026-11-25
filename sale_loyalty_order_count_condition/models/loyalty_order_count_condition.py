from odoo import fields, models


class LoyaltyOrderCountCondition(models.AbstractModel):
    """Shared order-count condition, usable on loyalty rules and programs."""

    _name = "loyalty.order.count.condition"
    _description = "Loyalty Order Count Condition"

    customer_order_condition = fields.Selection(
        selection=[
            ("first_ever", "Customer's first order"),
            ("first_use", "First order using this code"),
            ("repeat_ever", "Repeat order of the customer"),
            ("repeat_use", "Repeat order using this code"),
        ],
        string="Order Count Condition",
        help="Only apply when the customer's order count matches. Counts "
        "confirmed orders only. 'Using this code' counts orders on which a "
        "code of this rule/program was applied; the customer variants count "
        "all orders.",
    )

    def _customer_order_condition_met(self, order):
        self.ensure_one()
        if not self.customer_order_condition:
            return True
        partner = order.partner_id.commercial_partner_id
        if any(user._is_public() for user in partner.user_ids):
            # The order count cannot be known for an anonymous visitor.
            return False
        count = self._count_customer_prior_orders(order)
        if self.customer_order_condition.startswith("first"):
            return count == 0
        return count > 0

    def _customer_order_condition_message(self, order):
        self.ensure_one()
        partner = order.partner_id.commercial_partner_id
        if any(user._is_public() for user in partner.user_ids):
            return self.env._("Please log in to use this offer.")
        messages = {
            "first_ever": self.env._("This offer is only valid on your first order."),
            "first_use": self.env._("This code can only be used once per customer."),
            "repeat_ever": self.env._("This offer is only valid for repeat customers."),
            "repeat_use": self.env._("This code is only valid on a repeat order."),
        }
        return messages[self.customer_order_condition]

    def _count_customer_prior_orders(self, order):
        self.ensure_one()
        domain = [
            (
                "partner_id.commercial_partner_id",
                "=",
                order.partner_id.commercial_partner_id.id,
            ),
            ("state", "in", ["sale", "done"]),
        ]
        if self.customer_order_condition.endswith("_use"):
            domain += self._customer_order_condition_use_domain()
        return self.env["sale.order"].search_count(domain)

    def _customer_order_condition_use_domain(self):
        # What "using this code" means for the record type: override.
        self.ensure_one()
        return []
