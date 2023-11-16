# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    max_customer_application = fields.Integer(
        string="Maximum Customer Applications",
        default=0,
        help="Maximum times that a program can be applied to a customer. "
        "0 for no limit.",
    )
    salesmen_limit_ids = fields.One2many(
        string="Salesmen Limits",
        comodel_name="loyalty.salesmen.limit",
        inverse_name="program_id",
        help="Maximum times salesmen can apply a program. Empty for no limit.",
    )
    salesmen_strict_limit = fields.Boolean(
        default=False,
        string="Strict limit",
        help="If marked, promotion will only be allowed for the list of salesmen with "
        "their quantities",
    )
    salesmen_limit_count = fields.Integer(
        string="Salesmen maximum promotions",
        compute="_compute_salesmen_limit_count",
    )
    salesmen_limit_used_count = fields.Integer(
        string="Salesmen promotions used",
        compute="_compute_salesmen_limit_count",
    )

    @api.depends(
        "salesmen_limit_ids.max_salesman_application",
        "salesmen_limit_ids.times_used",
    )
    def _compute_salesmen_limit_count(self):
        """To be overriden"""
        self.salesmen_limit_count = 0
        self.salesmen_limit_used_count = 0


class LoyaltySalesmenLimit(models.Model):
    _name = "loyalty.salesmen.limit"
    _description = "Loyalty Salesmen limits"

    program_id = fields.Many2one(
        comodel_name="loyalty.program",
        auto_join=True,
        required=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesman",
        required=True,
        ondelete="cascade",
    )
    max_salesman_application = fields.Integer(
        string="Maximum Salesman Applications",
        default=0,
        help="Maximum times a salesman can apply a program. 0 for no limit.",
    )
    times_used = fields.Integer(
        string="Uses",
        compute="_compute_times_used",
    )

    _sql_constraints = [
        (
            "user_id_uniq",
            "unique(program_id, user_id)",
            "This salesman limit is already configured",
        ),
    ]

    @api.depends("user_id", "max_salesman_application")
    def _compute_times_used(self):
        """To be overriden"""
        self.times_used = 0
