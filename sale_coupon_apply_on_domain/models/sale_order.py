# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_values_percentage_amount(self, program):
        if program.discount_apply_on != "product_domain":
            return super()._get_reward_values_percentage_amount(program)
        # This is a partial copy of the original method for specific products
        # https://github.com/odoo/odoo/blob/14.0/\
        # addons/sale_coupon/models/sale_order.py#L257-L287
        # Patching was tried at first but this was generating too mucn
        # side effects with some other modules.

        reward_dict = {}
        lines = self._get_paid_order_lines()
        amount_total = sum(
            [
                any(line.tax_id.mapped("price_include"))
                and line.price_total
                or line.price_subtotal
                for line in self._get_base_order_lines(program)
            ]
        )
        # Here is the difference with the original method, we get the product ids
        # from the domain instead of the program.discount_specific_product_ids
        discount_specific_product_ids = program._get_discount_domain_product_ids(self)
        free_product_lines = (
            self.env["coupon.program"]
            .search(
                [
                    ("reward_type", "=", "product"),
                    (
                        "reward_product_id",
                        "in",
                        discount_specific_product_ids.ids,
                    ),
                ]
            )
            .mapped("discount_line_product_id")
        )
        lines = lines.filtered(
            lambda x: x.product_id
            in (discount_specific_product_ids | free_product_lines)
        )

        currently_discounted_amount = 0
        for line in lines:
            discount_line_amount = min(
                self._get_reward_values_discount_percentage_per_line(program, line),
                amount_total - currently_discounted_amount,
            )

            if discount_line_amount:
                if line.tax_id in reward_dict:
                    reward_dict[line.tax_id]["price_unit"] -= discount_line_amount
                else:
                    taxes = self.fiscal_position_id.map_tax(line.tax_id)

                    reward_dict[line.tax_id] = {
                        "name": _(
                            "Discount: %(program)s - "
                            "On product with following taxes: %(taxes)s",
                            program=program.name,
                            taxes=", ".join(taxes.mapped("name")),
                        ),
                        "product_id": program.discount_line_product_id.id,
                        "price_unit": -discount_line_amount
                        if discount_line_amount > 0
                        else 0,
                        "product_uom_qty": 1.0,
                        "product_uom": program.discount_line_product_id.uom_id.id,
                        "is_reward_line": True,
                        "tax_id": [(4, tax.id, False) for tax in taxes],
                    }
                    currently_discounted_amount += discount_line_amount

        max_amount = program._compute_program_amount(
            "discount_max_amount", self.currency_id
        )
        if max_amount > 0:
            amount_already_given = 0
            for val in list(reward_dict):
                amount_to_discount = (
                    amount_already_given + reward_dict[val]["price_unit"]
                )
                if abs(amount_to_discount) > max_amount:
                    reward_dict[val]["price_unit"] = -(
                        max_amount - abs(amount_already_given)
                    )
                    add_name = formatLang(
                        self.env, max_amount, currency_obj=self.currency_id
                    )
                    reward_dict[val]["name"] += "( " + _("limited to ") + add_name + ")"
                amount_already_given += reward_dict[val]["price_unit"]
                if reward_dict[val]["price_unit"] == 0:
                    del reward_dict[val]
        return reward_dict.values()
