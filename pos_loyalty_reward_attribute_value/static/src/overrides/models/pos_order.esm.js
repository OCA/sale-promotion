/* Copyright 2026 INVITU (<https://www.invitu.com>)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {patch} from "@web/core/utils/patch";

// Coupon of the reward being computed: the discountable helpers only receive
// the reward, while the number of rewarded units depends on the coupon points.
let attributeRewardContext = null;

patch(PosOrder.prototype, {
    _getRewardPtavIds(reward) {
        // Raw ids: product.template.attribute.value records of products not
        // loaded yet are not resolved as relations.
        return new Set(reward.raw?.discount_ptav_ids || []);
    },
    _getLineRewardedPriceExtra(line, ptavIds) {
        const ptavs = new Map();
        for (const ptav of [
            ...(line.attribute_value_ids || []),
            ...(line.product_id.product_template_variant_value_ids || []),
        ]) {
            if (ptavIds.has(ptav.id)) {
                ptavs.set(ptav.id, ptav);
            }
        }
        let extra = 0;
        for (const ptav of ptavs.values()) {
            extra += ptav.price_extra;
        }
        const unitPrice = line.get_unit_price();
        return Math.min(extra, unitPrice) * (1 - line.get_discount() / 100);
    },
    _isLineValidForAttributeReward(line) {
        return Boolean(
            line.get_quantity() &&
                line.isDiscountable() &&
                !line.is_reward_line &&
                !line.combo_parent_id &&
                !line.combo_line_ids?.length
        );
    },
    _getAttributeRewardUnits(reward, lines) {
        const ptavIds = this._getRewardPtavIds(reward);
        const units = [];
        for (const line of lines.filter((l) =>
            this._isLineValidForAttributeReward(l)
        )) {
            const extra = this._getLineRewardedPriceExtra(line, ptavIds);
            if (extra <= 0) {
                continue;
            }
            for (let i = 0; i < Math.floor(line.get_quantity()); i++) {
                units.push({line, extra});
            }
        }
        return units.sort((a, b) => b.extra - a.extra);
    },
    _getDiscountableOnAttributeValues(reward, lines) {
        const units = this._getAttributeRewardUnits(reward, lines);
        const points = this._getRealCouponPoints(attributeRewardContext.couponId);
        const maxUnits = reward.required_points
            ? Math.floor(points / reward.required_points)
            : units.length;
        const extraPerLine = new Map();
        for (const {line, extra} of units.slice(0, maxUnits)) {
            extraPerLine.set(line, (extraPerLine.get(line) || 0) + extra);
        }
        attributeRewardContext.units = Math.min(maxUnits, units.length);
        let discountable = 0;
        const discountablePerTax = {};
        for (const [line, extra] of extraPerLine) {
            const basePrice = line.get_base_price();
            if (!basePrice) {
                continue;
            }
            discountable += (line.get_price_with_tax() * extra) / basePrice;
            const taxKey = line.tax_ids
                .filter((t) => t.amount_type !== "fixed")
                .map((t) => t.id);
            discountablePerTax[taxKey] = (discountablePerTax[taxKey] || 0) + extra;
        }
        return {discountable, discountablePerTax};
    },
    _getDiscountableOnOrder(reward) {
        if (!attributeRewardContext || !this._getRewardPtavIds(reward).size) {
            return super._getDiscountableOnOrder(...arguments);
        }
        return this._getDiscountableOnAttributeValues(reward, this.get_orderlines());
    },
    _getDiscountableOnSpecific(reward) {
        if (!attributeRewardContext || !this._getRewardPtavIds(reward).size) {
            return super._getDiscountableOnSpecific(...arguments);
        }
        const productIds = new Set(reward.all_discount_product_ids.map((p) => p.id));
        return this._getDiscountableOnAttributeValues(
            reward,
            this.get_orderlines().filter((line) =>
                productIds.has(line.get_product().id)
            )
        );
    },
    _getRewardLineValuesDiscount(args) {
        const reward = args.reward;
        if (!this._getRewardPtavIds(reward).size) {
            return super._getRewardLineValuesDiscount(...arguments);
        }
        attributeRewardContext = {couponId: args.coupon_id, units: 0};
        try {
            const result = super._getRewardLineValuesDiscount(...arguments);
            if (Array.isArray(result) && result.length && !reward.clear_wallet) {
                result[0].points_cost =
                    attributeRewardContext.units * reward.required_points;
            }
            return result;
        } finally {
            attributeRewardContext = null;
        }
    },
});
