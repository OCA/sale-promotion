# Copyright 2024 (APSL-Nagarro) - Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import api, models


class LoyaltyCard(models.Model):
    _inherit = "loyalty.card"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record, vals in zip(res, vals_list, strict=True):
            if not vals.get("expiration_date", False):
                record._set_expiration_date()
        return res

    def _set_expiration_date(self):
        expiration = self._get_expiration_date()
        if expiration:
            self.expiration_date = expiration

    def _get_expiration_date(self):
        if self.program_id and self.program_id.duration_days > 0:
            return date.today() + timedelta(days=self.program_id.duration_days)
        return None
