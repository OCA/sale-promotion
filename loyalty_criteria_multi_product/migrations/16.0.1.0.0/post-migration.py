# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def _copy_multi_product_criteria(env):
    """Copy multi-product criteria to the new m2m table. Done this way for avoiding to
    rename columns, indexes, FKs, etc on the old m2m table, being this table not very
    big for sure.
    """
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO loyalty_criteria_product_product_rel
        (loyalty_criteria_id, product_product_id)
        SELECT coupon_criteria_id, product_product_id
        FROM coupon_criteria_product_product_rel
        """,
    )


def adapt_rules_with_repeat_product(env):
    """Adapt rules with the 'Repeat' option to new promotion rules.
    The functionality of the 'Repeat' option has been integrated into the rules
    of an Odoo promotion. This function adapts the existing loyalty criteria to
    the new structure.
    For each loyalty criterion with 'Repeat' enabled, the corresponding loyalty rule
    is updated with the minimum quantity and product information. After the update,
    the loyalty criterion is unlinked."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE loyalty_rule lr
        SET minimum_qty = lc.rule_min_quantity
        FROM loyalty_criteria lc
        WHERE lc.repeat_product
            AND lc.rule_id = lr.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO loyalty_rule_product_product_rel
        (loyalty_rule_id, product_product_id)
        SELECT lc.rule_id, rel2.product_product_id
        FROM loyalty_criteria_product_product_rel rel2
        JOIN loyalty_criteria lc ON lc.id = rel2.loyalty_criteria_id
        WHERE lc.repeat_product
        """,
    )
    openupgrade.logged_query(
        env.cr, "DELETE FROM loyalty_criteria WHERE repeat_product"
    )


@openupgrade.migrate()
def migrate(env, version):
    _copy_multi_product_criteria(env)
    adapt_rules_with_repeat_product(env)
