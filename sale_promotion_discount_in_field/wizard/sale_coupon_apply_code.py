from odoo import models
from odoo.osv import expression


class SaleCouponApplyCode(models.TransientModel):
    _inherit = "sale.coupon.apply.code"

    def apply_coupon(self, order, coupon_code):
        # OVERRIDE to apply the program to the order without reward lines
        program_domain = order._get_coupon_program_domain()
        additional_conditions = [
            ("promo_code", "=", coupon_code),
            ("reward_type", "=", "discount_line"),
            ("promo_applicability", "!=", "on_next_order"),
        ]
        program_domain = expression.AND([program_domain, additional_conditions])
        program = self.env["coupon.program"].search(program_domain)
        if program:
            error_status = program._check_promo_code(order, coupon_code)
            if not error_status:
                order._create_reward_line(program)
                order.code_promo_program_id = program
        else:
            return super().apply_coupon(order, coupon_code)
        return error_status
