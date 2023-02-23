# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    reward_type = fields.Selection(
        selection_add=[("free_product_domain", "Product Domain")],
        ondelete={"free_product_domain": "set default"},
    )
    reward_product_max_quantity = fields.Integer(
        string="Max reward quantity",
        default=0,
        help="Maximum reward product quantity (0 for no limit)",
    )

    def name_get(self):
        """Add complete description for the multi gift reward type."""
        free_product_domain_promo = self.filtered(
            lambda x: x.reward_type == "free_product_domain"
        )
        res = super(CouponReward, self - free_product_domain_promo).name_get()
        return res + [(p.id, _("Free Products")) for p in free_product_domain_promo]
