# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    def _compute_salesmen_limit_count(self):
        """This count is merely informative"""
        res = super()._compute_salesmen_limit_count()
        for program in self:
            program.salesmen_limit_count = sum(
                program.salesmen_limit_ids.mapped("max_salesman_application")
            )
            program.salesmen_limit_used_count = sum(
                program.salesmen_limit_ids.mapped("times_used")
            )
        return res


class LoyaltySalesmenLimit(models.Model):
    _inherit = "loyalty.salesmen.limit"

    def _compute_times_used(self):
        res = super()._compute_times_used()
        programs = self.env["loyalty.program"].search_read(
            [("id", "in", self.mapped("program_id").ids)],
            ["id", "program_type", "coupon_ids", "salesmen_limit_ids"],
        )
        for program in programs:
            salesmen_limits = self.filtered(
                lambda x: x._origin in program["salesmen_limit_ids"]
            )
            for salesman_limit in salesmen_limits:
                salesman_limit.times_used = len(
                    self.env["sale.order.line"].read_group(
                        [
                            ("loyalty_program_id", "=", program["id"]),
                            (
                                "order_id.user_id",
                                "=",
                                salesman_limit.user_id.id,
                            ),
                            ("order_id.state", "!=", "cancel"),
                        ],
                        ["order_id"],
                        ["order_id"],
                    )
                )
        return res
