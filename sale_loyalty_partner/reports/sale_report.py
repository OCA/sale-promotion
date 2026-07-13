# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    loyalty_program_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Loyalty Program Partner",
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["loyalty_program_partner_id"] = "scp.partner_id"
        return res

    def _from_sale(self):
        res = super()._from_sale()
        res += """ left join loyalty_program scp on (l.loyalty_program_id = scp.id)"""
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """, scp.partner_id"""
        return res
