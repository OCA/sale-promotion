# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO loyalty_reward_product_line_product_product_rel
            (loyalty_reward_product_line_id, product_product_id)
        SELECT coupon_reward_product_line_id, product_product_id
        FROM coupon_reward_product_line_product_product_rel
        """,
    )
