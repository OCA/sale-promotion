# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.fields import first


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_paid_order_lines(self):
        """Add reward lines produced by multi gift promotions"""
        lines = super()._get_paid_order_lines()
        free_reward_products = (
            self.env["coupon.program"]
            .search([("reward_type", "=", "multi_gift")])
            .mapped("coupon_multi_gift_ids.reward_product_ids")
        )
        free_reward_product_lines = self.order_line.filtered(
            lambda x: x.is_reward_line and x.product_id in free_reward_products
        )
        return lines | free_reward_product_lines

    def _get_reward_values_multi_gift_line(self, reward_line, program):
        """Multi Gift reward rules. For every gift reward rule, we'll create a new
        sale order line flagged as reward line with a 100% discount"""

        def _execute_onchanges(records, field_name):
            """Helper methods that executes all onchanges associated to a field."""
            for onchange in records._onchange_methods.get(field_name, []):
                for record in records:
                    onchange(record)

        # We could receive an optional product by context. Otherwise, the first product
        # will apply. This feature can be used by modules like
        # sale_coupon_selection_wizard.
        optional_product = (
            self.env["product.product"].browse(
                self.env.context.get("reward_line_options", {}).get(reward_line.id)
            )
            & reward_line.reward_product_ids
        )
        reward_product_id = optional_product or first(reward_line.reward_product_ids)
        # We prepare a new line and trigger the proper onchanges to ensure we get the
        # right line values (price unit according to the customer pricelist, taxes, ect)
        order_line = self.order_line.new(
            {"order_id": self.id, "product_id": reward_product_id.id}
        )
        _execute_onchanges(order_line, "product_id")
        order_line.update({"product_uom_qty": reward_line.reward_product_quantity})
        _execute_onchanges(order_line, "product_uom_qty")
        vals = order_line._convert_to_write(order_line._cache)
        vals.update(
            {
                "is_reward_line": True,
                "name": _("Free Product") + " - " + reward_product_id.name,
                "discount": 100,
                "coupon_program_id": program.id,
                "multi_gift_reward_line_id": reward_line.id,
                "multi_gift_reward_line_id_option_product_id": reward_product_id.id,
            }
        )
        return vals

    def _get_reward_values_multi_gift(self, program):
        """Wrapper to create the reward lines for a multi gift promotion"""
        return [
            self._get_reward_values_multi_gift_line(reward_line, program)
            for reward_line in program.coupon_multi_gift_ids
        ]

    def _get_reward_line_values(self, program):
        """Hook into the core method considering multi gift rewards"""
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == "multi_gift":
            return self._get_reward_values_multi_gift(program)
        return super()._get_reward_line_values(program)

    def _get_applicable_programs_multi_gift(self):
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
        enough granularity to avoid deleting the lines belonging to the multi gift
        programs when the promotions are updated. So the main module expects that the
        promotion lines products match with the promotion discount product
        (https://git.io/JWpoU) , which is not the approach in this module, where we add
        extra lines with the reward products themselves and the proper price tag and
        discount. So in this method override, we'll save those correct lines from the
        pyre via context that the unlink method will properly catch. We also have to
        remove the proper invalid lines that wouldn't be detected"""
        self.ensure_one()
        # This part is a repetition of the logic so we can get the right programs
        applied_programs = self._get_applied_programs()
        applicable_programs = self.env["coupon.program"]
        if applied_programs:
            applicable_programs = self._get_applicable_programs_multi_gift()
        programs_to_remove = applied_programs - applicable_programs
        # We're only interested in the Multi Gift programs
        multi_gift_applied_programs = applied_programs.filtered(
            lambda x: x.reward_type == "multi_gift"
        )
        # These will be the ones to keep
        valid_lines = self.order_line.filtered(
            lambda x: x.is_reward_line
            and x.coupon_program_id in multi_gift_applied_programs
        )
        multi_gift_programs_to_remove = programs_to_remove.filtered(
            lambda x: x.reward_type == "multi_gift"
        )
        if multi_gift_programs_to_remove:
            # Invalidate the generated coupons which we are not eligible anymore
            self.generated_coupon_ids.filtered(
                lambda x: x.program_id in multi_gift_programs_to_remove
            ).write({"state": "expired"})
            # Detect and remove the proper unvalid program order lines
            self.order_line.filtered(
                lambda x: x.is_reward_line
                and x.coupon_program_id in multi_gift_programs_to_remove
            ).unlink()
        # We'll catch the context in the subsequent unlink() method
        super(
            SaleOrder, self.with_context(valid_multi_gift_lines=valid_lines.ids)
        )._remove_invalid_reward_lines()

    def _update_existing_reward_lines(self):
        """We need to match `multi gift` programs with their discount product"""
        self.ensure_one()
        super(
            SaleOrder, self.with_context(only_reward_lines=True)
        )._update_existing_reward_lines()
        applied_programs = self._get_applied_programs_with_rewards_on_current_order()
        for program in applied_programs.filtered(
            lambda x: x.reward_type == "multi_gift"
        ):
            for reward_line in program.coupon_multi_gift_ids:
                lines = self.order_line.filtered(
                    lambda line: line.multi_gift_reward_line_id == reward_line
                    and line.is_reward_line
                    and line.coupon_program_id == program
                )
                applied_product = lines.multi_gift_reward_line_id_option_product_id
                for product in applied_product:
                    reward_line_options = {reward_line.id: product.id}
                    values = self.with_context(
                        reward_line_options=reward_line_options
                    )._get_reward_values_multi_gift_line(reward_line, program)
                    # Remove reward line if price or qty equal to 0
                    if values.get("product_uom_qty") and values.get("price_unit"):
                        lines.write(values)
                    else:
                        lines.unlink()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    multi_gift_reward_line_id = fields.Many2one(
        comodel_name="coupon.reward.product_line",
        readonly=True,
    )
    multi_gift_reward_line_id_option_product_id = fields.Many2one(
        comodel_name="product.product",
        readonly=True,
    )

    def unlink(self):
        """Avoid unlinking valid multi gift lines since they aren't linked to the
        discount product of the promotion program"""
        if not self.env.context.get("valid_multi_gift_lines"):
            return super().unlink()
        return super(
            SaleOrderLine,
            self.filtered(
                lambda x: x.id not in self.env.context.get("valid_multi_gift_lines")
            ),
        ).unlink()
