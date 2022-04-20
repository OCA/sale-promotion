# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    @api.onchange("reward_type")
    def _onchange_discount_line_reward_type(self):
        """
        Set discount type as discount if reward type is `discount_line`
        """
        if self.reward_type == "discount_line":
            if not self.env.user.has_group("product.group_discount_per_so_line"):
                raise UserError(
                    _(
                        "Please enable discount for sales order lines to set this reward type."
                    )
                )
            self.discount_type = "percentage"

    def _compute_order_count(self):
        discount_line_programs = self.filtered(
            lambda x: x.reward_type == "discount_line"
        )
        super(CouponProgram, self - discount_line_programs)._compute_order_count()
        sale_order_obj = self.env["sale.order"]
        for program in discount_line_programs:
            program.order_count = sale_order_obj.search_count(
                [
                    "|",
                    ("no_code_promo_program_ids", "in", program.ids),
                    ("code_promo_program_id", "in", program.ids),
                ],
            )

    def action_view_sales_orders(self):
        self.ensure_one()
        action = super(CouponProgram, self).action_view_sales_orders()
        if self.reward_type == "discount_line":
            orders = self.env["sale.order"].search(
                [
                    "|",
                    ("no_code_promo_program_ids", "in", self.ids),
                    ("code_promo_program_id", "in", self.ids),
                ],
            )
            action["domain"] = [("id", "in", orders.ids)]
        return action

    def _is_global_discount_program(self):
        discount_in_field_global = (
            self.promo_applicability == "on_current_order"
            and self.reward_type == "discount_line"
            and self.discount_type == "percentage"
            and self.discount_apply_on == "on_order"
        )
        return super()._is_global_discount_program() or discount_in_field_global
