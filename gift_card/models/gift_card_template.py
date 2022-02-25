# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gift_cart_template_ids = fields.One2many(
        "gift.card.template",
        "product_tmpl_id",
    )


class ProductTemplateGiftCard(models.Model):
    _name = "gift.card.template"
    _description = "Gift Card Templates"
    _inherits = {"product.template": "product_tmpl_id"}

    product_tmpl_id = fields.Many2one(
        "product.template", required=True, ondelete="cascade", string="Related Product"
    )

    is_divisible = fields.Boolean(default=True)
    duration = fields.Integer(string="Gift Card Duration (in months)", default=12)
    initial_amount = fields.Monetary()

    gift_card_count = fields.Integer(compute="_compute_gift_card_count")

    code_mask = fields.Char(
        help="Left Blanck for default value (XXXXXX-00): x means a "
        "random lowercase letter, X means a random uppercase letter, "
        "0 means a random digit. "
    )

    information = fields.Text()

    @api.model
    def _default_gift_card_journal_id(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("gift_card.gift_card_default_journal_id")
        )

    journal_id = fields.Many2one(
        "account.journal",
        string="Gift Card Journal",
        default=_default_gift_card_journal_id,
    )

    gift_card_ids = fields.One2many(
        "gift.card", "gift_card_tmpl_id", string="Gift Cards", copy=False
    )

    @api.depends("gift_card_ids")
    def _compute_gift_card_count(self):
        for template in self:
            gift_card_list = self.env["gift.card"].search(
                [("gift_card_tmpl_id", "=", template.id)]
            )
            if gift_card_list:
                template.gift_card_ids = gift_card_list.ids
                template.gift_card_count = len(gift_card_list.ids)
            else:
                template.gift_card_ids = []
                template.gift_card_count = 0

    def show_gift_cards(self):
        return {
            "name": "Gift Cards",
            "type": "ir.actions.act_window",
            "res_id": self.id,
            "view_mode": "form",
            "res_model": "gift.card",
            "view_id": False,
            "views": [
                (self.env.ref("gift_card.gift_card_tree_view").id, "tree"),
                (self.env.ref("gift_card.gift_card_form_view").id, "form"),
            ],
            "target": "current",
            "domain": [("id", "in", self.gift_card_ids.ids)],
        }
