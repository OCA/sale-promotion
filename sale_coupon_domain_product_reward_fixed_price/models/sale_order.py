from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _set_reward_fixed_price_for_lines(self, program):
        """
        Update discount field by program
        """
        if (
            program.discount_apply_on == "specific_products"
            and program.discount_apply_on_domain_product
        ):
            lines = (self.order_line - self._get_reward_lines()).filtered(
                lambda line: program._get_valid_products(line.product_id),
            )
            lines.write({"price_unit": program.price_unit})
        else:
            super()._set_reward_fixed_price_for_lines(program)
