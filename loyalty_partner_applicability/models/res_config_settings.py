# Copyright 2023 Tecnativa - Pilar Vargas Moreno
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    # Allows a coupon generated for one partner to be used by any other member
    # of your commercial entity. There is a view for this option in the module
    # sale_loyalty_partner_applicability
    allow_coupon_sharing = fields.Boolean(
        string="Allow coupon sharing",
        config_parameter="allow_coupon_sharing",
    )
