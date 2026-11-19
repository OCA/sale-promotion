/* Copyright 2026 INVITU (<https://www.invitu.com>)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/tours/utils/dialog_util";
import * as PosLoyalty from "@pos_loyalty/../tests/tours/utils/pos_loyalty_util";
import * as ProductConfigurator from "@point_of_sale/../tests/tours/utils/product_configurator_util";
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("PosLoyaltyRewardAttributeValueTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            ProductScreen.clickDisplayedProduct("Cup Drink"),
            ProductConfigurator.pickRadio("Big"),
            Dialog.confirm(),
            ProductScreen.clickDisplayedProduct("Variant Drink"),
            ProductConfigurator.pickRadio("Large"),
            Dialog.confirm(),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            PosLoyalty.hasRewardLine("Free option", "-100.00"),
            PosLoyalty.orderTotalIs("550.00"),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            PosLoyalty.hasRewardLine("Free option", "-150.00"),
            PosLoyalty.orderTotalIs("500.00"),
            Chrome.endTour(),
        ].flat(),
});

registry.category("web_tour.tours").add("PosLoyaltyRewardAttributeValueBottlesTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            ProductScreen.clickDisplayedProduct("Tea"),
            ProductConfigurator.pickRadio("Tapioca"),
            Dialog.confirm(),
            PosLoyalty.hasRewardLine("Free tapioca", "-100.00"),
            PosLoyalty.orderTotalIs("300.00"),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            ProductScreen.selectedOrderlineHas("Own Bottle", "4.00"),
            PosLoyalty.orderTotalIs("300.00"),
            PosLoyalty.isRewardButtonHighlighted(false, false),
            Chrome.endTour(),
        ].flat(),
});

registry.category("web_tour.tours").add("PosLoyaltyRewardAttributeValueEligibleTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            ProductScreen.clickDisplayedProduct("Own Bottle"),
            ProductScreen.clickDisplayedProduct("Tea"),
            ProductConfigurator.pickRadio("No topping"),
            Dialog.confirm(),
            PosLoyalty.hasRewardLine("Bottle", "-50.00"),
            PosLoyalty.orderTotalIs("250.00"),
            ProductScreen.clickDisplayedProduct("Dessert"),
            ProductConfigurator.pickRadio("Tapioca"),
            Dialog.confirm(),
            ProductScreen.selectedOrderlineHas("Dessert (Tapioca)", "1.00", "300.00"),
            PosLoyalty.orderTotalIs("550.00"),
            Chrome.endTour(),
        ].flat(),
});
