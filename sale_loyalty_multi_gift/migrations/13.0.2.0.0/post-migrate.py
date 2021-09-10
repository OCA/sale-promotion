# Copyright 2021 Tecnativa - David Vidal
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.m2o_to_x2m(
        env.cr,
        env["sale.coupon.reward.product_line"],
        "sale_coupon_reward_product_line",
        "reward_product_ids",
        openupgrade.get_legacy_name("reward_product_id"),
    )
