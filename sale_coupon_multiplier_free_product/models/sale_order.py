# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_paid_order_lines(self):
        """Returns the sale order lines that are not reward lines.
        It will also return reward lines being free product lines"""
        lines = super()._get_paid_order_lines()
        reward_multiple_of_lines = self.order_line.filtered(
            lambda x: x.coupon_program_id.reward_type == "multiple_of"
            and x.is_reward_line
        )
        return lines | reward_multiple_of_lines

    def _get_reward_line_values(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == "multiple_of":
            return [self._get_reward_values_multiple_of(program)]
        return super()._get_reward_line_values(program)

    def _get_reward_values_multiple_of(self, program):
        """Reward rules. The reward will be designed to give the rewarded product
        when the rule applies"""
        # The method `_is_valid_product` is in charge of evaluate whether or not
        # the product of the reward is the only one that applies.
        valid_lines = (self.order_line - self._get_reward_lines()).filtered(
            lambda x: program._get_valid_products(x.product_id)
        )
        applicable_qty = sum(valid_lines.mapped("product_uom_qty")) or 1
        rewardable_qty = applicable_qty // program.rule_min_quantity
        # We can set a maximum product reward quantity. By default is set to no limit
        if program.reward_product_max_quantity:
            rewardable_qty = min(rewardable_qty, program.reward_product_max_quantity)
        reward_product_qty = program.reward_product_quantity * rewardable_qty
        # Take the default taxes on the reward product,
        # mapped with the fiscal position
        taxes = program.reward_product_id.taxes_id
        if self.fiscal_position_id:
            taxes = self.fiscal_position_id.map_tax(taxes)
        # Compute the proper price_unit to create the new line accordingly. We just
        # create a virtual record in a similar way the ecommerce does as we just need
        # the price unit. The rest of the values will be prepared later in the method.
        # We used a test.Form() but with large orders it doesn't scale up very good.
        # At least in this version.
        line = self.env["sale.order.line"].new(
            {
                "order_id": self.id,
                "product_id": program.reward_product_id.id,
                "product_uom_qty": reward_product_qty,
            }
        )
        line.product_id_change()
        price_unit = line.price_unit
        return {
            "product_id": program.reward_product_id.id,
            "price_unit": price_unit,
            "product_uom_qty": reward_product_qty,
            "is_reward_line": True,
            "coupon_program_id": program.id,
            "name": _("Free Product") + " - " + program.reward_product_id.name,
            "discount": 100,
            "product_uom": program.reward_product_id.uom_id.id,
            "tax_id": [(4, tax.id, False) for tax in taxes],
        }

    def _update_existing_reward_lines(self):
        """We need to match `multiple_of` programs with their discount product"""
        self.ensure_one()
        res = super(
            SaleOrder, self.with_context(only_reward_lines=True)
        )._update_existing_reward_lines()
        applied_programs = self._get_applied_programs_with_rewards_on_current_order()
        for program in applied_programs.filtered(
            lambda x: x.reward_type == "multiple_of"
        ):
            values = self._get_reward_line_values(program)
            values = values and values[0]
            lines = self.order_line.filtered(
                lambda line: line.coupon_program_id == program and line.is_reward_line
            )
            # Remove reward line if price or qty equal to 0
            # if values.get("product_uom_qty") and values.get("price_unit"):
            if values.get("product_uom_qty"):
                lines.write(values)
            else:
                lines.unlink()
        return res

    def _get_applicable_programs_multiple_of(self):
        """Wrapper to avoid long method name limitations"""
        programs = (
            self._get_applicable_programs() + self._get_valid_applied_coupon_program()
        )
        programs = (
            programs._keep_only_most_interesting_auto_applied_global_discount_program()
        )
        return programs

    def _remove_invalid_reward_lines(self):
        """We have to put some logic redundancy here as the main method doesn't have
        enough granularity to avoid deleting the lines belonging to the multiplier
        programs when the promotions are updated. So the main module expects that the
        promotion lines products match with the promotion discount product
        (https://git.io/JWpoU) , which is not the approach in this module, where we add
        extra lines with the reward products themselves and the proper price tag and
        discount. So in this method override, we'll save those correct lines from the
        fire via context that the unlink method will properly catch. We also have to
        remove the proper invalid lines that wouldn't be detected"""
        self.ensure_one()
        # This part is a repetition of the logic so we can get the right programs
        applied_programs = self._get_applied_programs()
        applicable_programs = self.env["coupon.program"]
        if applied_programs:
            applicable_programs = self._get_applicable_programs_multiple_of()
        programs_to_remove = applied_programs - applicable_programs
        # We're only interested in the Multiplier programs
        multiple_of_applied_programs = applied_programs.filtered(
            lambda x: x.reward_type == "multiple_of"
        )
        # These will be the ones to keep
        valid_lines = self.order_line.filtered(
            lambda x: x.is_reward_line
            and x.coupon_program_id in multiple_of_applied_programs
        )
        multiple_of_programs_to_remove = programs_to_remove.filtered(
            lambda x: x.reward_type == "multiple_of"
        )
        if multiple_of_programs_to_remove:
            # Invalidate the generated coupons which we are not eligible anymore
            self.generated_coupon_ids.filtered(
                lambda x: x.program_id in multiple_of_programs_to_remove
            ).write({"state": "expired"})
            # Detect and remove the proper unvalid program order lines
            self.order_line.filtered(
                lambda x: x.is_reward_line
                and x.coupon_program_id in multiple_of_programs_to_remove
            ).unlink()
        # We'll catch the context in the subsequent unlink() method
        return super(
            SaleOrder, self.with_context(valid_multiple_of_lines=valid_lines)
        )._remove_invalid_reward_lines()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def write(self, vals):
        if not self.env.context.get("only_reward_lines"):
            return super().write(vals)
        return super(SaleOrderLine, self.filtered("is_reward_line")).write(vals)

    def unlink(self):
        """Avoid unlinking valid multiplier lines since they aren't linked to the
        discount product of the promotion program"""
        if not self.env.context.get("valid_multiple_of_lines"):
            return super().unlink()
        return super(
            SaleOrderLine,
            self.filtered(
                lambda x: x not in self.env.context.get("valid_multiple_of_lines")
            ),
        ).unlink()
