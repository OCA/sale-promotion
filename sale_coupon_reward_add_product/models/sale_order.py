# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _is_reward_in_order_lines(self, program):
        if not self.env.context.get("check_reward_in_order_lines", True):
            return True
        return super()._is_reward_in_order_lines(program)

    def _prepare_reward_product_line_vals(self, program):
        return {
            "order_id": self.id,
            "product_id": program.reward_product_id.id,
            "product_uom": program.reward_product_id.uom_id.id,
        }

    def _create_reward_line(self, program):
        # OVERRIDE to add the reward product to the order automatically
        if program.reward_product_add_if_missing:
            reward_product_lines = self.order_line.filtered(
                lambda line: line.product_id == program.reward_product_id
            )
            order_quantity = sum(reward_product_lines.mapped("product_uom_qty"))
            if order_quantity < program.reward_product_quantity:
                qty_to_add = float(program.reward_product_quantity) - order_quantity
                line_vals = self._prepare_reward_product_line_vals(program)
                line_vals.update(product_uom_qty=qty_to_add)
                line_vals.update(
                    self.env["sale.order.line"].play_onchanges(
                        line_vals, line_vals.keys()
                    )
                )
                self.env["sale.order.line"].create(line_vals)
        return super()._create_reward_line(program)
