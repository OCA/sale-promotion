# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleCouponRule(models.Model):
    _inherit = "sale.coupon.rule"

    rule_max_customer_application = fields.Integer(
        string="Maximum Customer Applications",
        default=0,
        help="Maximum times that a program can be applied to a customer. "
        "0 for no limit.",
    )
    rule_salesmen_limit_ids = fields.One2many(
        string="Salesmen Limits",
        comodel_name="sale.coupon.rule.salesmen.limit",
        inverse_name="rule_id",
        help="Maximum times salesmen can apply a program. Empty for no limit.",
    )
    rule_salesmen_strict_limit = fields.Boolean(
        default=False,
        string="Strict limit",
        help="If marked, promotion will only be allowed for the list of salesmen with "
        "their quantities",
    )
    rule_salesmen_limit_count = fields.Integer(
        string="Salesmen maximum promotions",
        compute="_compute_rule_salesmen_limit_count",
    )
    rule_salesmen_limit_used_count = fields.Integer(
        string="Salesmen promotions used", compute="_compute_rule_salesmen_limit_count",
    )

    @api.depends(
        "rule_salesmen_limit_ids.rule_max_salesman_application",
        "rule_salesmen_limit_ids.rule_times_used",
    )
    def _compute_rule_salesmen_limit_count(self):
        """This count is merely informative"""
        self.rule_salesmen_limit_count = 0
        self.rule_salesmen_limit_used_count = 0
        for rule in self:
            rule.rule_salesmen_limit_count = sum(
                rule.rule_salesmen_limit_ids.mapped("rule_max_salesman_application")
            )
            rule.rule_salesmen_limit_used_count = sum(
                rule.rule_salesmen_limit_ids.mapped("rule_times_used")
            )


class SaleCouponRuleSalesmenLimit(models.Model):
    _name = "sale.coupon.rule.salesmen.limit"
    _description = "Coupon Rule Salesmen limits"

    rule_id = fields.Many2one(
        comodel_name="sale.coupon.rule",
        auto_join=True,
        required=True,
        ondelete="cascade",
    )
    rule_user_id = fields.Many2one(
        comodel_name="res.users", string="Salesman", required=True, ondelete="cascade",
    )
    rule_max_salesman_application = fields.Integer(
        string="Maximum Salesman Applications",
        default=0,
        help="Maximum times a salesman can apply a program. 0 for no limit.",
    )
    rule_times_used = fields.Integer(string="Uses", compute="_compute_rule_times_used",)

    _sql_constraints = [
        (
            "user_id_uniq",
            "unique(rule_id, rule_user_id)",
            "This salesman limit is already configured",
        ),
    ]

    @api.depends("rule_user_id", "rule_max_salesman_application")
    def _compute_rule_times_used(self):
        """This count is also used in the check methods to avoid applying the rule
        above the salesmen limits."""
        self.rule_times_used = 0
        programs = self.env["sale.coupon.program"].search_read(
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
                        "sale.coupon"
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
                salesman_limit.rule_times_used = self.env["sale.order"].search_count(
                    [
                        "|",
                        ("no_code_promo_program_ids", "in", [program["id"]]),
                        ("code_promo_program_id", "=", [program["id"]]),
                        ("user_id", "=", salesman_limit.rule_user_id.id),
                    ]
                )
