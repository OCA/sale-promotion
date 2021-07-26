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

    @api.depends("rule_salesmen_limit_ids.rule_max_salesman_application")
    def _compute_rule_salesmen_limit_count(self):
        for rule in self:
            rule.rule_salesmen_limit_count = sum(
                rule.rule_salesmen_limit_ids.mapped(
                    "rule_salesmen_limit_ids.rule_max_salesman_application"
                )
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

    _sql_constraints = [
        (
            "user_id_uniq",
            "unique(rule_id, rule_user_id)",
            "This salesman limit is already configured",
        ),
    ]
