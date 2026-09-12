# FlousFlow Duplicate Detector

Maintained by [FlousFlow](https://flousflow.com) for Odoo 19 Community.

The package name is flousflow_duplicate_detector. Internal model names remain compatible with the original implementation.

Configurable duplicate detection for any Odoo model — warn users at the point of entry when the record they are saving already exists.

**Compatible with Odoo 19.0**

## Overview

Duplicate contacts, products, and vendors accumulate silently until they become a data quality crisis. This module adds configurable duplicate-checking rules to any Odoo model. Administrators define which model to watch and which fields to match. When a user saves a record that already exists in the system, they see an instant alert with the name of the existing record and a direct link to open it.

## Features

- **Per-Model Rules** — configure one rule per model. Watch Contacts, Products, Vendors, or any other model in your database. Each rule is independent and can be enabled or disabled at any time.
- **Multi-Field Matching** — select one or more fields per rule. All selected fields must match for a record to be flagged, giving precise control over what counts as a duplicate without false positives.
- **Direct Link to Duplicate** — the alert shows the name of the existing record and a clickable link to open it directly, so users can review it and decide whether to proceed or discard their entry.
- **Performance Optimized** — uses a `limit=1` search that stops at the first match. Works in milliseconds even on tables with 150,000+ records. Zero overhead when no rule is configured for a model.
- **Admin-Only Configuration** — rules are accessible only to system administrators (Settings → Technical → Duplicate Detector). Regular users see the warnings but cannot modify or disable the rules.
- **Import Safe** — checks run on every create, including imports and API calls.
- **Standard Field Highlighting** — required-field rules are checked before the
  save RPC; every missing field is marked with Odoo's native invalid-field
  styling so users can see exactly what to complete.
- **Required Field Rules** — define fields that must be completed for a model,
  independently from duplicate matching. The rule can be enabled per model,
  limited to selected users through an exemption group, and enforced during
  imports when required.
- **Two-Layer Validation** — the browser highlights missing fields before a
  save request is sent, while the server validates `create` and `write` as the
  final authority for API calls, imports, and other clients.
- **Three Duplicate Actions** — choose a warning dialog, a hard block, or a
  non-blocking notification that lets the record save while linking to the
  existing match.

## Installation

1. Add this repository folder to your `addons_path`.
2. Update the apps list (Apps → Update Apps List).
3. Search for **Duplicate Record Detector** and install.

## Configuration

1. Log in as a system administrator.
2. Go to **Settings → Technical → Duplicate Detector → Duplicate Rules**.
3. Create a rule: choose the **Model**, then pick the **Fields to Check** (stored, non-relational fields only).
4. Enable the rule. The check is active immediately on every save.

### Required field rules

1. Open **Settings → Technical → Duplicate Detector → Required Field Rules**.
2. Select a model and the fields that must be completed.
3. Optionally choose an **Exempt Group** for administrators or data-cleanup users.
4. Enable **Apply During Imports** only when incomplete imported rows should be rejected.

On a form, missing configured fields receive the same invalid styling used by
native Odoo required fields. The save is stopped before the RPC, and the server
performs the same check again for non-browser writes.

## Usage

- When a user saves a record whose selected fields all match an existing record, a blocking alert appears showing the existing record's name and a direct link to open it.
- The duplicate action is configurable: **Warning dialog**, **Block Save**, or
  **Notification only**.
- When a required-field rule finds empty values, the exact fields are marked in
  the form so the user knows what to complete; no failed save request is sent.
- Rules can be temporarily disabled with the **Active** toggle without deleting them.

## Technical Notes

- Checks are implemented on `models.AbstractModel` (`base`) via `create`/`write` overrides, with a context flag (`duplicate_skip`) to allow safe bypass when needed.
- The rule lookup uses `sudo()` because rules are technical configuration that all users are checked against.
- Works with any model; rule-per-model uniqueness is enforced at the database level.
- Required-field rules use the same per-model configuration pattern and are
  enforced in both the web client and the ORM layer.

## Included system screenshots

The Apps description includes real Odoo interface screenshots showing:

- The Technical menu entry and Duplicate Rules configuration screen.
- The duplicate alert displayed on a Contact form when a matching record is found.

The Required Field Rules section also documents the native field-level feedback
shown by Odoo before saving. Screenshots are kept separate from the module logic
so they can be replaced with customer-approved production captures later.

## License

LGPL-3 — see [LICENSE](LICENSE).
