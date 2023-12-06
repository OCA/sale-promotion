# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    discount_apply_on = fields.Selection(
        selection_add=[
            ("product_domain", "On Product Domain"),
        ]
    )
    discount_product_domain = fields.Char(
        string="Products Domain",
        default=[["sale_ok", "=", True]],
        help="The discount will apply on following products",
    )

    def name_get(self):
        # Add product_domain naming
        result = super().name_get()
        result_dict = dict(result)
        for reward in self:
            if (
                reward.reward_type == "discount"
                and reward.discount_type == "percentage"
                and reward.discount_apply_on == "product_domain"
            ):
                reward_percentage = str(reward.discount_percentage)
                # Since we do not have the order here we can't determine
                # on which products it will apply
                reward_string = _("%s%% discount on some products", reward_percentage)

                result_dict[reward.id] = reward_string

        return list(result_dict.items())
