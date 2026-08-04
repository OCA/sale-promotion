# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    reward_amount_tax_incl = fields.Float(compute="_compute_reward_total_tax_incl")
    promo_codes = fields.Char(compute="_compute_promo_codes")
    generated_coupon_ids = fields.One2many(
        "loyalty.card",
        "order_id",
        "Generated Coupons",
        help="The coupons generated from this order.",
    )
    program_ids = fields.Many2many(
        "loyalty.program", string="Applied programs", compute="_compute_programs"
    )

    def _get_reward_lines(self):
        self.ensure_one()
        return self.order_line.filtered("is_reward_line")

    @api.depends("order_line")
    def _compute_reward_total_tax_incl(self):
        for order in self:
            reward_amount_tax_incl = 0
            for line in order._get_reward_lines():
                if line.reward_id.reward_type != "product":
                    reward_amount_tax_incl += line.price_subtotal + line.price_tax
                else:
                    # Free product are 'regular' product lines with
                    # a price_subtotal and price_tax of 0
                    reward_amount_tax_incl -= line.product_id.taxes_id.compute_all(
                        line.product_id.lst_price,
                        product=line.product_id,
                        quantity=line.product_uom_qty,
                    )["total_included"]
            order.reward_amount_tax_incl = reward_amount_tax_incl

    @api.depends("order_line", "applied_coupon_ids", "code_enabled_rule_ids")
    def _compute_promo_codes(self):
        for order in self:
            codes = order.applied_coupon_ids.mapped(
                "code"
            ) + order.code_enabled_rule_ids.mapped("code")
            if codes:
                order.promo_codes = str(codes)  # stock the list of codes in a string
            else:
                order.promo_codes = "[]"

    @api.depends("order_line", "applied_coupon_ids", "code_enabled_rule_ids")
    def _compute_programs(self):
        self.program_ids = self.env["loyalty.program"]
        for order in self:
            order.program_ids = order.order_line.reward_id.program_id
