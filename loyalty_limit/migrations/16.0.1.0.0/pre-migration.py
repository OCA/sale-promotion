# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_field_renames = [
    ("loyalty.salesmen.limit", "loyalty_salesmen_limit", "rule_user_id", "user_id"),
    (
        "loyalty.salesmen.limit",
        "loyalty_salesmen_limit",
        "rule_max_salesman_application",
        "max_salesman_application",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(
        env.cr, [("coupon.rule.salesmen.limit", "loyalty.salesmen.limit")]
    )
    openupgrade.rename_tables(
        env.cr, [("coupon_rule_salesmen_limit", "loyalty_salesmen_limit")]
    )
    openupgrade.rename_fields(env.cr, _field_renames)
    # Create the 'program_id' field if it does not exist in the 'loyalty_salesmen_limit'
    # table and fill the 'program_id' field with values from 'loyalty_rule.program_id'
    # where 'loyalty_rule.id' is equal to old field 'loyalty_salesmen_limit.rule_id'
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE loyalty_salesmen_limit
        ADD COLUMN IF NOT EXISTS program_id INT
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE loyalty_salesmen_limit
        SET program_id = loyalty_rule.program_id
        FROM loyalty_rule
        WHERE loyalty_salesmen_limit.rule_id = loyalty_rule.id
        """,
    )
    # Delete constraints to recreate it
    openupgrade.delete_sql_constraint_safely(
        env, "loyalty_limit", "loyalty_salesmen_limit", "user_id_uniq"
    )
    # Move fields 'max_customer_application', 'salesmen_limit_ids' and 'salesmen_strict_limit'
    # from loyalty_rule to loyalty_program table
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE loyalty_program
        ADD COLUMN IF NOT EXISTS max_customer_application INT
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE loyalty_program
        ADD COLUMN IF NOT EXISTS salesmen_limit_ids INT
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE loyalty_program
        ADD COLUMN IF NOT EXISTS salesmen_strict_limit BOOLEAN
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE loyalty_program AS lp
        SET
            max_customer_application = lr.rule_max_customer_application,
            salesmen_limit_ids = lr.rule_salesmen_limit_ids,
            salesmen_strict_limit = lr.rule_salesmen_strict_limit
        FROM loyalty_rule AS lr
        WHERE lp.id = lr.program_id
        """,
    )
