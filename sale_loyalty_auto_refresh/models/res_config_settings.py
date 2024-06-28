# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auto_refresh_coupon = fields.Boolean(
        related="company_id.auto_refresh_coupon",
        readonly=False,
    )
