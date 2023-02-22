# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_paid_order_lines(self):
        """Add reward lines produced by free product from domain promotions"""
        lines = super()._get_paid_order_lines()
        free_product_domain_programs = self.env["coupon.program"].search(
            [("reward_type", "=", "free_product_domain")]
        )
        free_reward_product_lines = self.order_line.filtered(
            lambda x: x.is_reward_line
            and x.coupon_program_id in free_product_domain_programs
        )
        return lines | free_reward_product_lines

    def _get_reward_line_values(self, program):
        """Hook into the core method considering free product rewards"""
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == "free_product_domain":
            return self._get_reward_values_free_product_domain(program)
        return super()._get_reward_line_values(program)

    def _get_valid_products_free_product_domain(self, program):
        products = program._get_valid_products(
            self.order_line.filtered(lambda x: not x.is_reward_line).product_id
        )
        # For strict limits, every rewarded product must fulfill the general rule by
        # itself.
        if program.strict_per_product_limit:
            amount_field = (
                "price_subtotal"
                if program.rule_minimum_amount_tax_inclusion == "tax_excluded"
                else "price_tax"
            )
            for product in products:
                lines = self.order_line.filtered(lambda x: x.product_id == product)
                if not (
                    sum(lines.mapped("product_uom_qty")) >= program.rule_min_quantity
                    and sum(lines.mapped(amount_field)) >= program.rule_minimum_amount
                ):
                    products -= product
        return products

    def _get_reward_values_free_product_domain(self, program):
        """Wrapper to create the reward lines for a free products from domain promotion"""
        products = self._get_valid_products_free_product_domain(program)
        return [
            self._get_reward_values_free_product_domain_line(product, program)
            for product in products
        ]

    def _get_reward_values_free_product_domain_line(self, product, program):
        """Product domain reward rules. For every product we'll create a new
        sale order line flagged as reward line with a 100% discount"""

        def _execute_onchanges(records, field_name):
            """Helper methods that executes all onchanges associated to a field."""
            for onchange in records._onchange_methods.get(field_name, []):
                for record in records:
                    onchange(record)

        valid_lines = self.order_line - self._get_reward_lines()
        if program.strict_per_product_limit:
            valid_lines = valid_lines.filtered(lambda x: x.product_id == product)
        applicable_qty = sum(valid_lines.mapped("product_uom_qty")) or 1
        rewardable_qty = applicable_qty // program.rule_min_quantity
        # We can set a maximum product reward quantity. By default is set to no limit
        if program.reward_product_max_quantity:
            rewardable_qty = min(rewardable_qty, program.reward_product_max_quantity)
        reward_product_qty = program.reward_product_quantity * rewardable_qty
        # We prepare a new line and trigger the proper onchanges to ensure we get the
        # right line values (price unit according to the customer pricelist, taxes, ect)
        order_line = self.order_line.new(
            {"order_id": self.id, "product_id": product.id}
        )
        _execute_onchanges(order_line, "product_id")
        order_line.update({"product_uom_qty": reward_product_qty})
        _execute_onchanges(order_line, "product_uom_qty")
        vals = order_line._convert_to_write(order_line._cache)
        vals.update(
            {
                "is_reward_line": True,
                "name": _("Free Product") + " - " + program.name,
                "discount": 100,
                "coupon_program_id": program.id,
            }
        )
        return vals

    def _get_applicable_programs_free_product_domain(self):
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
        enough granularity to avoid deleting the lines belonging to the fred product
        domain programs when the promotions are updated. So the main module expects
        that the promotion lines products match with the promotion discount product
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
            applicable_programs = self._get_applicable_programs_free_product_domain()
        programs_to_remove = applied_programs - applicable_programs
        # We're only interested in the Multi Gift programs
        free_product_domain_applied_programs = applied_programs.filtered(
            lambda x: x.reward_type == "free_product_domain"
        )
        # These will be the ones to keep
        valid_lines = self.order_line.filtered(
            lambda x: x.is_reward_line
            and x.coupon_program_id in free_product_domain_applied_programs
        )
        free_product_domain_programs_to_remove = programs_to_remove.filtered(
            lambda x: x.reward_type == "free_product_domain"
        )
        if free_product_domain_programs_to_remove:
            # Invalidate the generated coupons which we are not eligible anymore
            self.generated_coupon_ids.filtered(
                lambda x: x.program_id in free_product_domain_programs_to_remove
            ).write({"state": "expired"})
            # Detect and remove the proper unvalid program order lines
            self.order_line.filtered(
                lambda x: x.is_reward_line
                and x.coupon_program_id in free_product_domain_programs_to_remove
            ).unlink()
        # We'll catch the context in the subsequent unlink() method
        res = super(
            SaleOrder,
            self.with_context(valid_free_product_domain_lines=valid_lines.ids),
        )._remove_invalid_reward_lines()
        return res

    def _update_existing_reward_lines(self):
        """We need to match `free_product_domain` programs with their discount product"""
        self.ensure_one()
        res = super(
            SaleOrder, self.with_context(only_reward_lines=True)
        )._update_existing_reward_lines()
        applied_programs = self._get_applied_programs_with_rewards_on_current_order()
        for program in applied_programs.filtered(
            lambda x: x.reward_type == "free_product_domain"
        ):
            lines = self.order_line.filtered(
                lambda line: line.is_reward_line and line.coupon_program_id == program
            )
            vals_list = self._get_reward_values_free_product_domain(program)
            lines_to_delete = lines.filtered(
                lambda l: l.product_id.id
                not in {v.get("product_id") for v in vals_list}
            )
            vals_list_to_create = []
            for values in vals_list:
                line = lines.filtered(
                    lambda x: x.product_id.id == values.get("product_id")
                )
                if not line:
                    vals_list_to_create.append(values)
                if values.get("product_uom_qty") and values.get("price_unit"):
                    line.write(values)
                    continue
                lines_to_delete += line
            lines_to_delete.unlink()
            if vals_list_to_create:
                self.write(
                    {"order_line": [(0, False, value) for value in vals_list_to_create]}
                )
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        """Avoid unlinking valid multi gift lines since they aren't linked to the
        discount product of the promotion program"""
        if not self.env.context.get("valid_free_product_domain_lines"):
            return super().unlink()
        return super(
            SaleOrderLine,
            self.filtered(
                lambda x: x.id
                not in self.env.context.get("valid_free_product_domain_lines")
            ),
        ).unlink()
