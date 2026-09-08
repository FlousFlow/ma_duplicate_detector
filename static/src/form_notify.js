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
