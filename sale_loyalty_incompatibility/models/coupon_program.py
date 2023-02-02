# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _check_promo_code(self, order, coupon_code):
        """Promotion incompatibility rules. Check the error strings for a detailed case
        detail."""
        message = super()._check_promo_code(order, coupon_code)
        # Other errors may precede
        if message:
            return message
        order_programs = order.no_code_promo_program_ids + order.code_promo_program_id
        order_programs |= (
            order.applied_coupon_ids + order.generated_coupon_ids
        ).mapped("program_id")
        if any({x in order_programs for x in self.incompatible_promotion_ids}):
            message = {
                "error": _(
                    "This promotion is incompatible with other set already in the "
                    "order so it can't be applied."
                )
            }
        return message
