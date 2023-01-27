# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class CouponRule(models.Model):
    _inherit = "coupon.rule"

    def _compute_rule_salesmen_limit_count(self):
        """This count is merely informative"""
        res = super()._compute_rule_salesmen_limit_count()
        for rule in self:
            rule.rule_salesmen_limit_count = sum(
                rule.rule_salesmen_limit_ids.mapped("rule_max_salesman_application")
            )
            rule.rule_salesmen_limit_used_count = sum(
                rule.rule_salesmen_limit_ids.mapped("rule_times_used")
            )
        return res


class CouponRuleSalesmenLimit(models.Model):
    _inherit = "coupon.rule.salesmen.limit"

    def _compute_rule_times_used(self):
        """This count is also used in the check methods to avoid applying the rule
        above the salesmen limits."""
        res = super()._compute_rule_times_used()
        programs = self.env["coupon.program"].search_read(
            [("rule_id", "in", self.mapped("rule_id").ids)],
            ["id", "rule_id", "program_type", "coupon_ids", "rule_salesmen_limit_ids"],
        )
        coupon_programs = [
            p
            for p in programs
            if p["program_type"]
            and p["program_type"] == "coupon_program"
            or p["coupon_ids"]
        ]
        for program in programs:
            salesmen_limits = self.filtered(
                lambda x: x._origin.id in program["rule_salesmen_limit_ids"]
            )
            for salesman_limit in salesmen_limits:
                if program in coupon_programs and not program["coupon_ids"]:
                    continue
                elif program in coupon_programs:
                    salesman_limit.rule_times_used = self.env[
                        "coupon.coupon"
                    ].search_count(
                        [
                            ("program_id", "=", program["id"]),
                            ("state", "=", "used"),
                            (
                                "sales_order_id.user_id",
                                "=",
                                salesman_limit.rule_user_id.id,
                            ),
                        ]
                    )
                    continue
                # We need to ensure that the promotion is indeed applied in the lines
                # since a link in the sale.order can have traces of promotion links
                # even when their lines are removed. This needs to look in the related
                # user_id column of the sale_order table, so maybe not the most
                # performant query. It can be improved in the future.
                salesman_limit.rule_times_used = len(
                    self.env["sale.order.line"].read_group(
                        [
                            ("coupon_program_id", "=", program["id"]),
                            ("order_id.user_id", "=", salesman_limit.rule_user_id.id),
                            ("state", "!=", "cancel"),
                        ],
                        ["order_id"],
                        ["order_id"],
                    )
                )
        return res
