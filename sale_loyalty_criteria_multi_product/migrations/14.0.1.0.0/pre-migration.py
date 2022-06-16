# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_field_renames = [
    (
        "coupon.program",
        "coupon_program",
        "sale_coupon_criteria",
        "coupon_criteria",
    ),
    (
        "coupon.program",
        "coupon_program",
        "sale_coupon_criteria_ids",
        "coupon_criteria_ids",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
