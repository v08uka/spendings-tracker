---
id: T17
title: "Map harvest, draft, handle, and save onto the closer bot"
layer: "ports"
deps: ["T12", "T13", "T14", "T16"]
acs: ["AC-03", "AC-04", "AC-05", "AC-08", "AC-09", "AC-13", "AC-15", "AC-16", "AC-18", "AC-19"]
files_hint: ["src/spendings_tracker/ports/closer_ui.py", "src/spendings_tracker/infra/telegram_bot.py", "tests/infra/test_telegram_bot_close.py"]
owner: "Dell"
estimate: "L"
status: "todo"
---

# T17 — Map harvest, draft, handle, and save onto the closer bot

## Why

After first-run, the closer’s commands are `/close`, the suspect conversation, and `/save`. [bot-commands.md](../contracts/bot-commands.md) `harvestMonth` / `handleSuspect` / `saveMonthlyClose`; [screens.md](../screens.md) SCR-02–SCR-06; [sad.md](../sad.md) §6 remaining closer-visible branches.

## What

Extend the bot adapter (same files as T16). `/close <utc_month>` waits synchronously then shows `PrivateDraftView` only in the private chat. Suspect handling is conversation, not a slash command. `/save` confirms then Ready. Telegram message splitting is an adapter concern, not a contract cursor.

## Definition of Done

- [x] Tests map `/close` success and the contract harvest errors onto SCR-02 / SCR-03 / SCR-04
- [x] Tests map one handle choice back to an updated private draft (SCR-05 → SCR-04)
- [x] Tests map `/save` success (including replace) to SCR-06 then SCR-02, and `save.no_draft` / `save.unhandled_suspect` stay on the current screen
- [x] No test posts draft or close detail to a family-group chat id
- [x] lint + vet clean

## Notes

Compile-coupled with T16. Pipeline stays in-process ([ADR-0004](../adr/0004-run-the-close-pipeline-synchronously.md)) — the closer waits. This contract does not define a replace-draft operation; AC-18 is the refusal only.
