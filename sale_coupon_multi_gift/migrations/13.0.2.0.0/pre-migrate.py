# Copyright 2021 Tecnativa - David Vidal
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "sale_coupon_reward_product_line", "reward_product_id"
    ):
        openupgrade.rename_columns(
            env.cr, {"sale_coupon_reward_product_line": [("reward_product_id", None)]}
        )
