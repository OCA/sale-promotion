# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval


class CouponReward(models.Model):
    _inherit = "coupon.reward"
    # Now the main field is a non stored field. We'll be storing former records for
    # regular behavior a special sibling stored field
    discount_specific_product_ids = fields.Many2many(
        compute="_compute_discount_specific_product_ids",
        inverse="_inverse_discount_specific_product_ids",
        search="_search_discount_specific_product_ids",
        readonly=False,
        store=False,
    )
    # This is where we'll store our real products for regular promos. Indeed, we're
    # taking the former relation in order to keep former data. This saves us
    # supercomplex init/uninstall hooks +1 for the ORM
    stored_discount_specific_product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="product_product_sale_coupon_reward_rel",
    )
    discount_apply_on_domain_product = fields.Boolean(
        string="Apply on products domain",
        help="When set, the discount will be applied on the filtered products",
    )

    @api.depends("discount_apply_on_domain_product")
    @api.depends_context("promo_domain_product")
    def _compute_discount_specific_product_ids(self):
        """When receiving the proper context, the field will work dinamically.
        Otherwise it just masks the stored field"""
        domain_product = self.env.context.get("promo_domain_product")
        if domain_product:
            self.discount_specific_product_ids = list(
                self.env["product.product"]._search(safe_eval(domain_product))
            )
            return
        for reward in self:
            reward.discount_specific_product_ids = (
                reward.stored_discount_specific_product_ids
            )

    def _inverse_discount_specific_product_ids(self):
        """If we set the products manually we'll dismiss this setting"""
        for reward in self:
            reward.stored_discount_specific_product_ids = (
                reward.discount_specific_product_ids
            )

    def _search_discount_specific_product_ids(self, operator, value):
        domain_product = self.env.context.get("promo_domain_product")
        if domain_product:
            return [
                (
                    "id",
                    "in",
                    self.env["product.product"]._search(safe_eval(domain_product)),
                )
            ]
        return [("stored_discount_specific_product_ids", operator, value)]

    def name_get(self):
        """We don't know from this model the domain set on the rule. A generic name
        is given"""
        discount_domain_product_rewards = self.filtered(
            lambda reward: reward.reward_type == "discount"
            and reward.discount_apply_on == "specific_product"
            and reward.discount_apply_on_domain_product
        )
        result = super(CouponReward, self - discount_domain_product_rewards).name_get()
        if discount_domain_product_rewards:
            result += [
                (
                    reward.id,
                    _(
                        "%s%% discount on selected products",
                        str(reward.discount_percentage),
                    ),
                )
                for reward in discount_domain_product_rewards
            ]
        return result
