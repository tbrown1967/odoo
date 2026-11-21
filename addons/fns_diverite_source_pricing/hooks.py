from odoo.exceptions import UserError


_FIELDS = {
    "x_fns_diverite_map_price": "float",
    "x_fns_diverite_partner_price": "float",
    "x_fns_diverite_source": "char",
}
_VIEWS = {
    "product_source_prices_form": "product.product_template_form_view",
    "product_source_prices_list": "product.product_template_tree_view",
}


def pre_init_hook(env):
    """Adopt legacy metadata in place. Odoo reflects declared fields by model and name."""
    internal = env.ref("base.group_user")
    existing_fields = env["ir.model.fields"].search([
        ("model", "=", "product.template"), ("name", "in", list(_FIELDS)),
    ])
    for field in existing_fields:
        if (
            field.state != "manual"
            or field.ttype != _FIELDS[field.name]
            or not field.readonly
            or field.copied
            or field.company_dependent
            or field.groups != internal
        ):
            raise UserError(f"Cannot adopt the existing Dive Rite field {field.name} safely.")

    metadata = env["ir.model.data"]
    for name, parent in _VIEWS.items():
        legacy = metadata.search([("module", "=", "fns_diverite"), ("name", "=", name)])
        if not legacy:
            continue
        view = env["ir.ui.view"].browse(legacy.res_id).exists() if legacy.model == "ir.ui.view" else False
        if (
            not view
            or view.model != "product.template"
            or view.inherit_id != env.ref(parent)
            or not all(field in view.arch_db for field in _FIELDS)
            or env.ref(f"fns_diverite_source_pricing.{name}", raise_if_not_found=False)
        ):
            raise UserError(f"Cannot adopt the existing Dive Rite view {name} safely.")
        legacy.write({"module": "fns_diverite_source_pricing", "noupdate": False})
