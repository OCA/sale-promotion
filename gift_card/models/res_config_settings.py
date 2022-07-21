# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_gift_card = fields.Boolean("Gift Cards", default=True)
    gift_card_default_journal_id = fields.Many2one(
        "account.journal",
        string="Default Gift Card Journal",
        config_parameter="gift_card.gift_card_default_journal_id",
        help="Default Journal used for Gift Cards payments",
    )
