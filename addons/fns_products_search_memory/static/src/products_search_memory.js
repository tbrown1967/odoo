import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { user } from "@web/core/user";
import { hashCode } from "@web/core/utils/strings";
import { patch } from "@web/core/utils/patch";
import { SearchModel } from "@web/search/search_model";
import { session } from "@web/session";

const PRODUCTS_ACTION = "stock.product_template_action_product";
const MAX_STATE_SIZE = 128 * 1024;
const memories = new WeakMap();

function memoryFor(model, config) {
    const action = model.env.config;
    const context = config.context || {};
    const { domain, groupBy, orderBy } = router.current;
    if (
        action?.actionXmlId !== PRODUCTS_ACTION ||
        config.resModel !== "product.template" ||
        !session.db ||
        !user.userId ||
        action.currentEmbeddedActionId ||
        config.domain?.length ||
        config.groupBy?.length ||
        config.orderBy?.length ||
        domain ||
        groupBy ||
        orderBy ||
        context.active_id ||
        context.active_ids?.length ||
        Object.keys(context).some(
            (key) =>
                (key.startsWith("search_default_") && key !== "search_default_goods") ||
                key.startsWith("searchpanel_default_")
        )
    ) {
        return null;
    }

    const companies = context.allowed_company_ids || user.context.allowed_company_ids || [];
    const defaults = (config.irFilters || []).filter((favorite) => favorite.is_default);
    return {
        key: `fns.products.search.v1:${session.db}:${user.userId}:${action.actionId}:${companies.join(",")}`,
        signature: hashCode(JSON.stringify([
            config.searchViewId,
            config.searchViewArch,
            Object.keys(config.searchViewFields || {}).sort(),
            context.lang || user.context.lang,
            context.search_default_goods,
            defaults,
        ])),
    };
}

function readState({ key, signature }) {
    try {
        const raw = browser.localStorage.getItem(key);
        if (!raw || raw.length > MAX_STATE_SIZE) {
            return null;
        }
        const saved = JSON.parse(raw);
        if (
            saved.signature === signature &&
            Array.isArray(saved.state?.query) &&
            saved.state.searchItems &&
            saved.state.searchPanelInfo &&
            Array.isArray(saved.state.sections)
        ) {
            return saved.state;
        }
    } catch {
        // A corrupt or unavailable browser store should leave the native search usable.
    }
    return null;
}

patch(SearchModel.prototype, {
    async load(config) {
        memories.delete(this);
        const memory = memoryFor(this, config);
        const remembered = memory && !config.state && readState(memory);
        if (remembered) {
            try {
                await super.load({ ...config, state: remembered });
                // Validate the restored filter and group expressions before the view reads them.
                void this.domain;
                void this.groupBy;
                memories.set(this, memory);
                return;
            } catch {
                try {
                    browser.localStorage.removeItem(memory.key);
                } catch {
                    // Storage restrictions also prevent future reuse.
                }
            }
        }
        await super.load(config);
        if (memory) {
            memories.set(this, memory);
        }
    },

    async _notify() {
        await super._notify();
        const memory = memories.get(this);
        if (!memory || this.blockNotification) {
            return;
        }
        try {
            const raw = JSON.stringify({
                signature: memory.signature,
                state: this.exportState(),
            });
            if (raw.length <= MAX_STATE_SIZE) {
                browser.localStorage.setItem(memory.key, raw);
            } else {
                browser.localStorage.removeItem(memory.key);
            }
        } catch {
            // Search still works when browser storage is disabled or full.
        }
    },
});
