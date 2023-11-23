# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def adapt_rules_with_repeat_product(env):
    """Adapt rules with the 'Repeat' option to new promotion rules.
    The functionality of the 'Repeat' option has been integrated into the rules
    of an Odoo promotion. This function adapts the existing loyalty criteria to
    the new structure.
    For each loyalty criterion with 'Repeat' enabled, the corresponding loyalty rule
    is updated with the minimum quantity and product information. After the update,
    the loyalty criterion is unlinked."""
    env.cr.execute("SELECT id FROM loyalty_criteria WHERE repeat_product = true")
    results = env.cr.fetchall()
    loyalty_criteria_ids = [result[0] for result in results]
    for loyalty_criteria in env["loyalty.criteria"].browse(loyalty_criteria_ids):
        rule = env["loyalty.rule"].browse(loyalty_criteria.rule_id)
        rule.minimum_qty = loyalty_criteria.rule_min_quantity
        rule.product_ids = rule.product_ids
        loyalty_criteria.unlink()
    env.cr.commit()


@openupgrade.migrate()
def migrate(env, version):
    adapt_rules_with_repeat_product(env)
