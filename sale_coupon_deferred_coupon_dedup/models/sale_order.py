# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    unconfirmed_applied_coupon_ids = fields.Many2many(
        "coupon.coupon",
        relation="coupon_coupon_unconfirmed_sale_order_rel",
        help="Coupons that should be applied at this order confirmation",
        readonly=True,
    )

    def action_confirm(self):
        # Set all unconfirmed coupons as confirmed for order
        for coupon in self.unconfirmed_applied_coupon_ids:
            # Check if they are still valid
            if coupon.state not in ["new", "sent"]:
                raise UserError(
                    _("This coupon has already been used (%s).") % (coupon.code)
                )

            self.applied_coupon_ids += coupon

        # Clear all unconfirmed on confirmation
        self.unconfirmed_applied_coupon_ids = [(6, 0, [])]
        return super().action_confirm()

    def action_cancel(self):
        # Remove all unconfirmed coupon from order
        self.unconfirmed_applied_coupon_ids = [(6, 0, [])]
        return super().action_cancel()

    # Most of the remaining code is duplication of applied_coupon_ids logic to
    # unconfirmed_applied_coupon_ids

    def _is_global_discount_already_applied(self):
        # Add unconfirmed coupon programs to this getter
        return (
            super()._is_global_discount_already_applied()
            + self.unconfirmed_applied_coupon_ids.mapped("program_id").filtered(
                lambda program: program._is_global_discount_program()
            )
        )

    def _get_valid_applied_coupon_program(self):
        # Add unconfirmed coupon programs to this getter
        programs = super()._get_valid_applied_coupon_program()
        programs |= (
            self.unconfirmed_applied_coupon_ids.mapped("program_id")
            .filtered(lambda p: p.promo_applicability == "on_next_order")
            ._filter_programs_from_common_rules(self, True)
        )
        programs |= (
            self.unconfirmed_applied_coupon_ids.mapped("program_id")
            .filtered(lambda p: p.promo_applicability == "on_current_order")
            ._filter_programs_from_common_rules(self)
        )

        return programs

    def _remove_invalid_reward_lines(self):
        # Remove also unconfirmed coupons from programs
        self.ensure_one()

        super()._remove_invalid_reward_lines()

        # The programs_to_remove computations are sadly duplicated from parent
        order = self
        applied_programs = order._get_applied_programs()
        applicable_programs = self.env["coupon.program"]
        if applied_programs:
            applicable_programs = (
                order._get_applicable_programs()
                + order._get_valid_applied_coupon_program()
            )
            applicable_programs = (
                applicable_programs._keep_only_most_interesting_auto_applied_global_discount_program()  # noqa
            )
        programs_to_remove = applied_programs - applicable_programs

        if programs_to_remove:
            # This is the custom behavior
            unconfirmed_coupons_to_remove = (
                order.unconfirmed_applied_coupon_ids.filtered(
                    lambda coupon: coupon.program_id in programs_to_remove
                )
            )

            if unconfirmed_coupons_to_remove:
                order.unconfirmed_applied_coupon_ids -= unconfirmed_coupons_to_remove

    def _get_applied_programs_with_rewards_on_current_order(self):
        # Add unconfirmed coupon programs to this getter
        applied_programs = super()._get_applied_programs_with_rewards_on_current_order()
        code_promo_programs = self.code_promo_program_id.filtered(
            lambda p: p.promo_applicability == "on_current_order"
        )
        # Insert unconfirmed coupons just after applied coupons and before code promo
        # NB super() order is
        # self.no_code_promo_program_ids
        # self.applied_coupon_ids.mapped('program_id')
        # self.code_promo_program_id

        applied_programs = (
            (applied_programs - code_promo_programs)
            | (self.unconfirmed_applied_coupon_ids.mapped("program_id"))
            | code_promo_programs
        )

        return applied_programs

    def _get_applied_programs(self):
        # Add unconfirmed coupon programs to this getter
        return (
            super()._get_applied_programs()
            + self.unconfirmed_applied_coupon_ids.mapped("program_id")
        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        # Start by removing unconfirmed coupons from the order
        for line in self.filtered(lambda line: line.is_reward_line):
            removed_unconfirmed_coupon = (
                line.order_id.unconfirmed_applied_coupon_ids.filtered(
                    lambda coupon: coupon.program_id.discount_line_product_id
                    == line.product_id
                )
            )
            line.order_id.unconfirmed_applied_coupon_ids -= removed_unconfirmed_coupon

        return super().unlink()
