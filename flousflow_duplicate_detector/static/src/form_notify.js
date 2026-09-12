/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

/**
 * Non-blocking duplicate notification ('notify' rule action).
 *
 * The list of models having an active 'notify' rule is fetched ONCE per
 * web-client session, so saves on models without rules cost zero extra RPC.
 * (If an admin adds a rule mid-session, reload the browser to activate it.)
 */
let maNotifyModels = null;
const maRequiredFieldsByModel = new Map();

async function getNotifyModels(orm) {
    if (maNotifyModels === null) {
        try {
            maNotifyModels = new Set(
                await orm.silent.call(
                    "ma.duplicate.rule",
                    "get_notify_models",
                    [],
                ),
            );
        } catch {
            maNotifyModels = new Set();
        }
    }
    return maNotifyModels;
}

async function getRequiredFields(orm, modelName) {
    if (!maRequiredFieldsByModel.has(modelName)) {
        try {
            const fields = await orm.silent.call(
                "ma.required.field.rule",
                "get_required_field_names",
                [modelName],
            );
            maRequiredFieldsByModel.set(modelName, new Set(fields || []));
        } catch {
            // A missing/old module on another database must never block saves.
            maRequiredFieldsByModel.set(modelName, new Set());
        }
    }
    return maRequiredFieldsByModel.get(modelName);
}

function isEmptyRequiredValue(record, fieldName) {
    const field = record.fields[fieldName];
    const value = record.data[fieldName];
    if (!field) {
        // The field is not part of this form view, so there is no widget to
        // highlight. The server-side check remains authoritative.
        return false;
    }
    if (["one2many", "many2many"].includes(field.type)) {
        return !value || !value.count;
    }
    if (field.type === "many2one") {
        return !value || !value.id;
    }
    return value === false || value === null || value === undefined || value === "";
}

function hasCapturedCoordinates(record) {
    return Boolean(record.data.partner_latitude && record.data.partner_longitude);
}

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.maNotification = useService("notification");
    },

    async onWillSaveRecord(record, params) {
        const result = await super.onWillSaveRecord(record, params);
        if (result === false) {
            return false;
        }

        const requiredFields = await getRequiredFields(this.orm, record.resModel);
        const missingFields = [];
        for (const fieldName of requiredFields) {
            // GPS capture backfills these server-side; reverse-geocoding may
            // legitimately leave them empty when the provider is unavailable.
            if (
                hasCapturedCoordinates(record) &&
                ["country_id", "state_id"].includes(fieldName)
            ) {
                continue;
            }
            if (isEmptyRequiredValue(record, fieldName)) {
                missingFields.push(fieldName);
            }
        }
        if (missingFields.length) {
            for (const fieldName of missingFields) {
                await record.setInvalidField(fieldName);
            }
            // Keep the same standard invalid-field styling/notification used
            // by native required fields, without sending a doomed RPC.
            await record.checkValidity({ displayNotification: true });
            return false;
        }

        const notifyModels = await getNotifyModels(this.orm);
        if (!notifyModels.has(record.resModel)) {
            return true;
        }
        try {
            const duplicate = await this.orm.silent.call(
                record.resModel,
                "ma_check_duplicate",
                [record._getChanges()],
            );
            if (duplicate) {
                this.maNotification.add(
                    duplicate.name,
                    Object.assign(
                        {
                            title: "Duplicate Detected",
                            type: "warning",
                            sticky: false,
                        },
                        duplicate.id
                            ? {
                                  message: duplicate.name,
                                  buttons: [
                                      {
                                          name: "Open",
                                          onClick: () => {
                                              this.actionService.doAction({
                                                  type: "ir.actions.act_window",
                                                  res_model: record.resModel,
                                                  res_id: duplicate.id,
                                                  view_mode: "form",
                                                  target: "current",
                                              });
                                          },
                                      },
                                  ],
                              }
                            : {}
                    ),
                );
            }
        } catch {
            // never block a save because the check itself failed
        }
        return true;
    },
});
