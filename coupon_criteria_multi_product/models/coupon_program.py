# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    coupon_criteria = fields.Selection(
        selection=[("domain", "Domain"), ("multi_product", "Multi Product")],
        string="Coupon criteria",
        help="- Domain: Standard behavior. The products are evaluated by domain.\n"
        "- Multi product: different rules can be applied to different products "
        "and all of the have to be fulfilled",
        default="domain",
    )
    coupon_criteria_ids = fields.One2many(
        string="Multi Product Criterias",
        comodel_name="coupon.criteria",
        inverse_name="program_id",
    )

    @api.onchange("coupon_criteria")
    def _onchange_coupon_criteria(self):
        """Clear domain so we clear some other fields from the view"""
        if self.coupon_criteria == "multi_product":
            self.rule_products_domain = False

    def _get_valid_products_multi_product(self, products, criteria):
        """Return valid products depending on the criteria repeat product setting. Then
        the main method will check if the minimum quantities are acomplished."""
        if criteria.repeat_product:
            return products.browse(
                [x.id for x in criteria.product_ids if x in products]
            )
        if not all([x in products for x in criteria.product_ids]):
            return self.env["product.product"]
        return criteria.product_ids
