---
id: T16
title: "Map first-run and AuthZ onto the closer bot"
layer: "ports"
deps: ["T11"]
acs: ["AC-01", "AC-02", "AC-06", "AC-14"]
files_hint: ["src/spendings_tracker/ports/closer_ui.py", "src/spendings_tracker/infra/telegram_bot.py", "tests/infra/test_telegram_bot_first_run.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T16 — Map first-run and AuthZ onto the closer bot

## Why

Closer UI is a bot private chat; anyone else and the family group must not see draft or close detail. [spec §AC-01](../spec.md); [spec §AC-02](../spec.md); [spec §AC-06](../spec.md); [spec §AC-14](../spec.md); [ADR-0003](../adr/0003-use-bot-ui-and-user-session-harvest.md); [ADR-0006](../adr/0006-split-closer-ui-and-harvest-ports.md); [screens.md](../screens.md) SCR-01, SCR-07; [bot-commands.md](../contracts/bot-commands.md) `completeFirstRun` and AuthZ convention.

## What

Fold `CloserUiPort` into this task. Implement the Telegram bot adapter for `/start` first-run (SCR-01 default / validation / error) and Unauthorized (SCR-07). Family-group inbound is silence — no draft, no refusal, no close detail posted there.

## Definition of Done

- [x] Tests drive the first-run wizard to Ready (SCR-02) on a valid confirm
- [x] Empty list and close-before-confirm map to the contract error messages
- [x] A non-closer addressing the bot gets `auth.not_closer` with no draft or close detail; group inbound is unanswered
- [x] lint + vet clean

## Notes

Compile-coupled with T17 — both list `closer_ui.py` and `telegram_bot.py`. No `ui` layer: `target_surfaces` is `[backend-service]`. Conversation states come from [screens.md](../screens.md); do not invent a web/mobile screen.
