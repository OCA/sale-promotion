import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

export class SuggestPromotionWidget extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }
    getSuggestedPromotions() {
        return this.props.record.data.suggested_reward_ids.records.map(
            (object) => object.evalContext.id
        );
    }

    async viewPromotionsWizard() {
        const productId = this.props.record.data.product_id[0];
        const SuggestedPromotions = this.getSuggestedPromotions();
        const record = this.__owl__.parent.parent.parent.parent.props.record;
        await record.save();
        this.actionService.doAction("sale_loyalty.sale_loyalty_reward_wizard_action", {
            additionalContext: {
                default_active_id: record.evalContext.id,
                default_order_id: record.evalContext.id,
                default_product_id: productId,
                default_reward_ids: SuggestedPromotions,
            },
        });
    }
}

SuggestPromotionWidget.template = "sale_loyalty_order_suggestion.suggestPromotion";
SuggestPromotionWidget.props = standardFieldProps;

registry
    .category("fields")
    .add("suggest_promotion_widget", {component: SuggestPromotionWidget});
