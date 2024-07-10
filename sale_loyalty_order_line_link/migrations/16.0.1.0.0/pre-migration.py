# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_renamed_fields = [
    (
        "sale.order.line",
        "sale_order_line",
        "coupon_program_id",
        "loyalty_program_id",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE sale_order_line
        ADD COLUMN IF NOT EXISTS reward_id INTEGER;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE sale_order_line AS sol
        SET reward_id = lr.id
        FROM loyalty_reward AS lr
        WHERE sol.loyalty_program_id = lr.program_id;
        """,
    )
