/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

/**
 * Non-blocking duplicate notification ('notify' rule action).
 * Before the record is saved, ask the server whether the current changes
 * would match an active Duplicate Rule. If so, save anyway but show a
 * warning notification with a link to the existing record.
 */
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
