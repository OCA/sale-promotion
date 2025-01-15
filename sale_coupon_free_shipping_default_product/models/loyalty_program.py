from odoo import api, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if "reward_ids" in val:
                for item in val["reward_ids"]:
                    if (
                        "reward_type" in item[2]
                        and item[2]["reward_type"] == "shipping"
                    ):  # val is a tuple
                        product = self.env.company.free_shipping_product_default
                        if product:
                            item[2]["discount_line_product_id"] = product.id
        program = super(LoyaltyProgram, self).create(vals_list)

        return program
