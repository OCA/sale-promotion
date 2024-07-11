# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_renamed_fields = [
    (
        "loyalty.reward",
        "loyalty_reward",
        "coupon_multi_gift_ids",
        "loyalty_multi_gift_ids",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
    openupgrade.rename_models(
        env.cr, [("coupon.reward.product_line", "loyalty.reward.product_line")]
    )
    openupgrade.rename_tables(
        env.cr, [("coupon_reward_product_line", "loyalty_reward_product_line")]
    )
