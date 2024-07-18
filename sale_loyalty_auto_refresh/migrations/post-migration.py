# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def update_parameter_key(env):
    parameters = env["ir.config_parameter"].search(
        [("key", "like", "sale_coupon_auto_refresh.")]
    )
    for parameter in parameters:
        parameter.key = (parameter.key).replace(
            "sale_coupon_auto_refresh.", "sale_loyalty_auto_refresh."
        )


@openupgrade.migrate()
def migrate(env, version):
    update_parameter_key(env)
