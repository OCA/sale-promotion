# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class LoyaltyProgram(models.Model):

    _inherit = "loyalty.program"

    beneficiary_partner_type = fields.Selection(
        string="Beneficiary Partner",
        selection=[
            ("partner", "Customer"),
            ("invoiced_partner", "Invoiced Customer"),
            ("commercial_entity", "Commercial Entity"),
        ],
        default="partner",
        help="The the partner that will be the beneficiary of the program\n"
        "- Customer: the customer of the sale order\n"
        "- Invoiced Customer: the invoiced partner of the sale order\n"
        "- Commercial Entity: the commercial entity of the customer of the sale order",
    )
