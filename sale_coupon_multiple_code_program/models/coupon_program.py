# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression


class SaleCouponProgram(models.Model):
    _inherit = "coupon.program"

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """HACK: Allow to use multiple code coupon programs

        Adding this condition we can fool the core filters to allow multiple
        code programs in a single order. They get registered in the
        no_code_promo_program_ids but aside from that they'll behave as regular code
        programs."""
        if self.env.context.get("discard_no_code_programs_with_code"):
            args = expression.AND([[("promo_code", "=", False)], args or []])
        return super().search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
        )
