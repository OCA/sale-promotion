# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def move_coupon_criteria_to_rule(env):
    """Move everything related to coupon.criteria from the loyalty.program model to
    loyalty.rule."""
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE loyalty_rule
        ADD COLUMN IF NOT EXISTS loyalty_criteria CHAR
        """,
    )
    # Set the value of "lotalty_rule.loyalty_criteria" previously defined in
    # "coupon_program.coupon_criteria".
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE loyalty_rule AS lr
        SET loyalty_criteria = 'multi_product'
        FROM loyalty_program AS lp
        WHERE lr.program_id = lp.id
        AND lp.coupon_criteria = 'multi_product'
        """,
    )
    # coupon_criteria_ids to loyalty_criteria_ids
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE loyalty_criteria
        ADD COLUMN IF NOT EXISTS rule_id INT
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE loyalty_criteria
        SET rule_id = loyalty_rule.id
        FROM loyalty_rule
        WHERE
            loyalty_rule.program_id = loyalty_criteria.program_id
            AND loyalty_rule.loyalty_criteria = 'multi_gift'
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, [("coupon.criteria", "loyalty.criteria")])
    openupgrade.rename_tables(env.cr, [("coupon_criteria", "loyalty_criteria")])
    move_coupon_criteria_to_rule(env)
