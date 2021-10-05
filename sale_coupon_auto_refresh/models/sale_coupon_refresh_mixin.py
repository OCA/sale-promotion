# Copyright 2021 Tecnativa - David Vidal
# Copyright 2021 Camptocamp - Silvio Gregorini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleCouponRefreshMixin(models.AbstractModel):
    _name = "sale.coupon.refresh.mixin"
    _description = "Mixin class for sale coupon auto-refresh features"

    auto_refresh_coupon_triggers_data = fields.Binary(
        attachment=False,
        compute="_compute_auto_refresh_coupon_triggers_data",
        store=False,
    )

    @api.model
    def _get_auto_refresh_coupons_triggers(self) -> set:
        """Returns set of fields which trigger the recomputation

        Hook method to be overridden if necessary
        """
        return set()

    @api.depends(lambda self: list(self._get_auto_refresh_coupons_triggers()))
    def _compute_auto_refresh_coupon_triggers_data(self):
        triggers = self._get_auto_refresh_coupons_triggers()
        for rec in self:
            data = dict()
            for dotted_field_name in triggers:
                val = rec.mapped(dotted_field_name)
                if isinstance(val, models.AbstractModel):
                    val = val.ids
                data[dotted_field_name] = val
            rec.auto_refresh_coupon_triggers_data = data

    def _read_recs_data(self) -> list:
        """Reads `auto_refresh_coupon_triggers_data` for all records in `self`

        :return: list of dicts:

            [{"id": x, "auto_refresh_coupon_triggers_data": y}]

            each dict representing a different record (as a result
            of `self.read()`)
            The list is sorted by "id" key.
        """
        return sorted(
            self.read(["auto_refresh_coupon_triggers_data"]), key=lambda d: d["id"]
        )

    def _check_skip_refresh(self):
        """Checks whether refresh should be skipped

        Hook method to be overridden if necessary
        :return: True if auto-refresh should be skipped
        """
        ctx = self.env.context
        # Checking for `website_id` because `website_sale_coupon` already
        # refreshes coupons on every cart_update and every checkout
        # controller reload
        # NB: no need to add `website_sale_coupon` as dependency since we
        # only use it for this context flag
        return ctx.get("skip_auto_refresh_coupons") or ctx.get("website_id")
