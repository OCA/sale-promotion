# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_values_discount(self, program):
        if program.discount_apply_on != "domain_product":
            return super()._get_reward_values_discount(program)

        lines = (self.order_line - self._get_reward_lines()).filtered(
            lambda line: program._get_valid_products(line.product_id),
        )

        # when processing lines we should not discount more than the order remaining total
        currently_discounted_amount = 0
        reward_dict = {}
        amount_total = sum(self._get_base_order_lines(program).mapped("price_subtotal"))
        for line in lines:
            discount_line_amount = min(
                self._get_reward_values_discount_percentage_per_line(program, line),
                amount_total - currently_discounted_amount,
            )
            if discount_line_amount:
                if line.tax_id in reward_dict:
                    reward_dict[line.tax_id]["price_unit"] -= discount_line_amount
                else:
                    reward_dict[line.tax_id] = self._get_reward_values_for_tax(
                        line, program, discount_line_amount
                    )
                    currently_discounted_amount += discount_line_amount

        # If there is a max amount for discount, we might have to limit
        # some discount lines or completely remove some lines
        max_amount = program._compute_program_amount(
            "discount_max_amount", self.currency_id
        )
        if max_amount > 0:
            reward_dict = self._get_final_amount(reward_dict, max_amount)
        return reward_dict.values()

    def _get_reward_values_for_tax(self, line, program, discount_line_amount):
        taxes = self.fiscal_position_id.map_tax(line.tax_id)
        uom_id = program.discount_line_product_id.uom_id.id
        return {
            "name": _(
                "Discount: %(program)s - On product with following " "taxes: %(taxes)s",
                program=program.name,
                taxes=", ".join(taxes.mapped("name")),
            ),
            "product_id": program.discount_line_product_id.id,
            "price_unit": -discount_line_amount if discount_line_amount > 0 else 0,
            "product_uom_qty": 1.0,
            "product_uom": uom_id,
            "is_reward_line": True,
            "tax_id": [(4, tax.id, False) for tax in taxes],
        }

    def _get_final_amount(self, reward_dict, max_amount):
        amount_already_given = 0
        _reward_dict = reward_dict.copy()
        for tax in reward_dict.keys():
            amount_to_discount = amount_already_given + _reward_dict[tax]["price_unit"]
            if abs(amount_to_discount) > max_amount:
                _reward_dict[tax]["price_unit"] = -(
                    max_amount - abs(amount_already_given)
                )
                add_name = formatLang(
                    self.env, max_amount, currency_obj=self.currency_id
                )
                _reward_dict[tax]["name"] += _("(limited to %s)", add_name)
            amount_already_given += _reward_dict[tax]["price_unit"]
            if _reward_dict[tax]["price_unit"] == 0:
                del _reward_dict[tax]
        return _reward_dict
