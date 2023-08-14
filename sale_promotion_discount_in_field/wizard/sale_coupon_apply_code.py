from odoo import models
from odoo.osv import expression


class SaleCouponApplyCode(models.TransientModel):
    _inherit = "sale.coupon.apply.code"

    def apply_coupon(self, order, coupon_code):
        # OVERRIDE to apply the program to the order without reward lines
        error_status = {}
        program_domain = order._get_coupon_program_domain()
        program_domain = expression.AND(
            [program_domain, [("promo_code", "=", coupon_code)]]
        )
        program = self.env["coupon.program"].search(program_domain)
        if (
            program
            and program.reward_type == "discount_line"
            and program.promo_applicability != "on_next_order"
        ):
            error_status = program._check_promo_code(order, coupon_code)
            if not error_status:
                order._create_reward_line(program)
                order.code_promo_program_id = program
        else:
            return super().apply_coupon(order, coupon_code)
        return error_status
