from odoo import api, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    @api.model
    def _program_type_default_values(self):
        """
        Override to set communication plan trigger to 'never' for coupon programs.
        """
        result = super()._program_type_default_values()
        comm_plans = result["coupons"]["communication_plan_ids"]
        for plan in comm_plans:
            if plan[0] == 0:
                plan[2]["trigger"] = "never"

        return result
