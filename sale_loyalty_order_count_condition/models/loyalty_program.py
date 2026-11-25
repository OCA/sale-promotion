from odoo import api, models


class LoyaltyProgram(models.Model):
    _name = "loyalty.program"
    _inherit = ["loyalty.program", "loyalty.order.count.condition"]

    def _customer_order_condition_use_domain(self):
        return [("code_enabled_rule_ids.program_id", "=", self.id)]

    @api.model
    def _get_template_values(self):
        # The Referral template gets the first-order condition at program
        # level: every code minted under it shares the policy.
        values = super()._get_template_values()
        if "referral" in values:
            values["referral"]["customer_order_condition"] = "first_ever"
        return values
