# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_values_discount_strict_limit_lines(self, program):
        """We'll restrict the domain to only the products fulfilling individually the
        criterias"""
        domain = program.rule_products_domain
        program = program.with_context(promo_domain_product=domain)
        extendable_domain = safe_eval(domain)
        intersected_products = self.order_line.product_id & self.env[
            "product.product"
        ].search(extendable_domain)
        amount_field = (
            "price_subtotal"
            if program.rule_minimum_amount_tax_inclusion == "tax_excluded"
            else "price_tax"
        )
        intersected_lines = self.env["sale.order.line"]
        for product in intersected_products:
            product_lines = self.order_line.filtered(
                lambda x: x.product_id == product and not x.is_reward_line
            )
            if (
                sum(product_lines.mapped("product_uom_qty"))
                >= program.rule_min_quantity
                and sum(product_lines.mapped(amount_field))
                >= program.rule_minimum_amount
            ):
                intersected_lines |= product_lines
        # Prepare the extended domain to send it by context
        domain = str(
            expression.AND(
                [
                    extendable_domain,
                    [("id", "in", intersected_lines.product_id.ids or [0])],
                ]
            )
        )
        return domain

    def _get_reward_values_discount(self, program):
        """We simply inject the context in order to gather the proper discounted
        products according to the current domain"""
        if (
            program.discount_apply_on_domain_product
            and program.discount_apply_on == "specific_products"
        ):
            domain = program.rule_products_domain
            # In this case, we need to preevaluate the domain along with every line
            # affected
            if program.strict_per_product_limit:
                domain = self._get_reward_values_discount_strict_limit_lines(program)
            return super()._get_reward_values_discount(
                program.with_context(promo_domain_product=domain)
            )
        return super()._get_reward_values_discount(program)
