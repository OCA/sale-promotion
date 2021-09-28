# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.tests import Form


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
        # Compute the proper price_unit to create the new line accordingly.
        # We use the form class to ensure the proper onchanges.
        sale_form = Form(self)
        with sale_form.order_line.new() as line:
            line.product_id = program.reward_product_id
            line.product_uom_qty = program.reward_product_quantity
            price_unit = line.price_unit
        # The method `_is_valid_product` is in charge of evaluate whether or not
        # the product of the reward is the only one that applies.
        valid_lines = (self.order_line - self._get_reward_lines()).filtered(
            lambda x: program._is_valid_product(x.product_id)
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
        super(
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
            if values.get("product_uom_qty") and values.get("price_unit"):
                lines.write(values)
            else:
                lines.unlink()

    def _remove_invalid_reward_lines(self):
        """Inject context to avoid removing the wrong lines"""
        return super(
            SaleOrder, self.with_context(only_reward_lines=True)
        )._remove_invalid_reward_lines()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def write(self, vals):
        if not self.env.context.get("only_reward_lines"):
            return super().write(vals)
        return super(SaleOrderLine, self.filtered("is_reward_line")).write(vals)

    def unlink(self):
        reward_lines = self.filtered("is_reward_line").exists()
        for line in reward_lines:
            related_program = self.env["sale.coupon.program"].search(
                [("reward_product_id", "=", line.product_id.id)]
            )
            line.order_id.no_code_promo_program_ids -= related_program
            line.order_id.code_promo_program_id -= related_program
        if not self.env.context.get("only_reward_lines"):
            return super(SaleOrderLine, self.exists()).unlink()
        return super(SaleOrderLine, reward_lines).unlink()
