/** @odoo-module **/

import {Order} from "point_of_sale.models";
import Registries from "point_of_sale.Registries";

const PosLoyaltyOrder = (Order) =>
    class PosLoyaltyOrder extends Order {
        _getDiscountableOnSpecific(reward) {
            let {discountable, discountablePerTax} = super._getDiscountableOnSpecific(
                ...arguments
            );
            const applicableProducts = reward.all_discount_product_ids;
            const linesToDiscount = [];
            const orderLines = this.get_orderlines();
            const remainingAmountPerLine = {};
            for (const line of orderLines) {
                if (!line.get_quantity() || !line.price) {
                    continue;
                }
                remainingAmountPerLine[line.cid] = line.get_price_with_tax();
                if (
                    applicableProducts.has(line.get_product().id) ||
                    (line.reward_product_id &&
                        applicableProducts.has(line.reward_product_id))
                ) {
                    linesToDiscount.push(line);
                }
            }

            var reward_attributes = reward.discount_attribute_ids.map((attr) => attr);
            for (const line of linesToDiscount) {
                const attribute_values = _.flatten(
                    line.product.attribute_line_ids.map((id) =>
                        this.pos.attributes_by_ptal_id[id].values.map((v) => v)
                    )
                );
                if (
                    reward.limit_discounted_attributes &&
                    reward.limit_discounted_attributes !== "disabled"
                ) {
                    line.product_no_variant_attribute_value_ids.forEach((value_id) => {
                        const attribute_val = attribute_values.find(
                            (value) => value.id === value_id
                        );
                        if (!reward_attributes.includes(attribute_val.attribute_id)) {
                            discountable -= attribute_val.price_extra;
                        }
                    });
                    if (reward.limit_discounted_attributes === "attributes") {
                        discountable -= line.product.lst_price;
                    }
                    const taxKey = line.get_taxes().map((t) => t.id);
                    if (!discountablePerTax[taxKey]) {
                        discountablePerTax[taxKey] = 0;
                    }
                    discountablePerTax[taxKey] = discountable;
                }
            }
            return {discountable, discountablePerTax};
        }
    };

Registries.Model.extend(Order, PosLoyaltyOrder);
