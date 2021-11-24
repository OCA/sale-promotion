# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from odoo import _, api, models
from odoo.osv.expression import is_leaf


@contextmanager
def temporary_update(record, vals):
    """Temporarily update values on a record, revert on exit"""
    prev_vals = {fname: record[fname] for fname in vals.keys()}
    with record.env.protecting(vals.keys(), record):
        record.update(vals)
        yield
        record.update(prev_vals)


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _check_promo_code(self, order, coupon_code):
        # OVERRIDE to check validity against commitment date.
        # This method is not easily overriden so to have super() ignore the original
        # check against date_order by temporarily unsetting the rule_date_from/to fields
        if (
            self.rule_date_field == "date_order"
            or not (self.rule_date_from or self.rule_date_to)
            or not order[self.rule_date_field]
            or order[self.rule_date_field] == order.date_order
        ):
            return super()._check_promo_code(order, coupon_code)
        # Check if the coupon is valid for this commitment_date. Fail-fast if not.
        if (
            self.rule_date_from
            and self.rule_date_from > order[self.rule_date_field]
            or self.rule_date_to
            and order[self.rule_date_field] > self.rule_date_to
        ):
            return {"error": _("Promo code is expired")}
        # Temporarily unset the rule_date_from/to fields and call super()
        # This will check all other rules, but the date_order check will be ignored.
        with temporary_update(self, {"rule_date_from": False, "rule_date_to": False}):
            return super()._check_promo_code(order, coupon_code)

    @api.model
    def _filter_on_validity_dates(self, order):
        # OVERRIDE to check validity against commitment date.
        records = self.filtered(lambda rec: rec.rule_date_field != "date_order")
        regular_records = self - records
        res = super(CouponProgram, regular_records)._filter_on_validity_dates(order)
        res |= records.filtered(
            lambda rec: (
                (
                    not rec.rule_date_from
                    or rec.rule_date_from
                    <= (order[rec.rule_date_field] or order.date_order)
                )
                and (
                    not rec.rule_date_to
                    or rec.rule_date_to
                    >= (order[rec.rule_date_field] or order.date_order)
                )
            )
        )
        # Apply an id-based filter on self to keep the original recordset's order
        return self.filtered(lambda rec: rec in res)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # OVERRIDE to handle the commitment date on the original promotion domain,
        # when called from :meth:`sale_order._get_applicable_no_code_promo_program`
        # or :meth:`sale_order._get_applicable_programs`.
        #
        # The original domain looks like this:
        #
        #   [
        #       ...
        #       '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', date),
        #       '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', date),
        #       ...
        #   ]
        #
        # The resulting domain should be:
        #
        #   [
        #       ...
        #       '|', ('rule_date_from', '=', False),
        #           '|',
        #               '&',
        #               ('rule_date_field', '=', 'date_order'),
        #               ('rule_date_from', '<=', date),
        #               '&',
        #               ('rule_date_field', '=', 'commitment_date'),
        #               ('rule_date_from', '<=', commitment_date),
        #       '|', ('rule_date_to', '=', False),
        #           '|',
        #               '&',
        #               ('rule_date_field', '=', 'date_order'),
        #               ('rule_date_to', '<=', date),
        #               '&',
        #               ('rule_date_field', '=', 'commitment_date'),
        #               ('rule_date_to', '<=', commitment_date),
        #       ...
        #   ]
        commitment_date = self.env.context.get("coupon_rule_commitment_date")
        if commitment_date:
            new_domain = []
            for element in args:
                if is_leaf(element):
                    left, operator, __ = element
                    if left in ["rule_date_from", "rule_date_to"] and operator != "=":
                        new_domain += [
                            "|",
                            "&",
                            ("rule_date_field", "=", "date_order"),
                            element,
                            "&",
                            ("rule_date_field", "=", "commitment_date"),
                            (left, operator, commitment_date),
                        ]
                        continue
                new_domain.append(element)
            args = new_domain
        return super().search(
            args, offset=offset, limit=limit, order=order, count=count
        )
