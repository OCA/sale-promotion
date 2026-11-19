/* Copyright 2026 INVITU (<https://www.invitu.com>)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/tours/utils/dialog_util";
import * as Order from "@point_of_sale/../tests/tours/utils/generic_components/order_widget_util";
import * as PosLoyalty from "@pos_loyalty/../tests/tours/utils/pos_loyalty_util";
import * as ProductConfigurator from "@point_of_sale/../tests/tours/utils/product_configurator_util";
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("PosLoyaltyOrderLineChangeVariantTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            ProductScreen.clickDisplayedProduct("Tea"),
            ProductConfigurator.pickRadio("Large"),
            Dialog.confirm(),
            PosLoyalty.hasRewardLine("Large discount", "-30.00"),
            PosLoyalty.orderTotalIs("270.00"),
            ProductScreen.selectedOrderlineHas("Tea (Large)", "1.00"),
            {
                trigger:
                    '.order-container .orderline.selected:has(.product-name:contains("Tea (Large)"))',
                run: "click",
            },
            ProductConfigurator.pickRadio("Regular"),
            Dialog.confirm(),
            ProductScreen.selectedOrderlineHas("Tea (Regular)", "1.00"),
            Order.doesNotHaveLine({productName: "Large discount"}),
            PosLoyalty.orderTotalIs("300.00"),
            Chrome.endTour(),
        ].flat(),
});
