from odoo import models


class LoyaltyRule(models.Model):
    _name = "loyalty.rule"
    _inherit = ["loyalty.rule", "loyalty.order.count.condition"]

    def _customer_order_condition_use_domain(self):
        return [("code_enabled_rule_ids", "in", self.id)]
