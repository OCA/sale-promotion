# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class Coupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order_date, partner_id, **kwargs):
        """Coupon incompatibility rules. Check the error strings for a detailed case
        detail."""
        message = super()._check_coupon_code(order_date, partner_id, **kwargs)
        order = kwargs.get("order", False)
        # Other errors may precede
        if message:
            return message
        order_programs = order.no_code_promo_program_ids + order.code_promo_program_id
        order_programs |= (
            order.applied_coupon_ids + order.generated_coupon_ids
        ).mapped("program_id")
        if any(
            {x in order_programs for x in self.program_id.incompatible_promotion_ids}
        ):
            message = {
                "error": _(
                    "This promotion is incompatible with other set already in the "
                    "order so it can't be applied."
                )
            }
        return message
