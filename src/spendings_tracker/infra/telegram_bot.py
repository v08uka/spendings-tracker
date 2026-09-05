"""Telegram bot adapter for the closer's private chat."""

from __future__ import annotations

from datetime import datetime

from spendings_tracker.app.complete_first_run import (
    complete_first_run,
    require_first_run,
)
from spendings_tracker.app.errors import AppError, catalog_error
from spendings_tracker.app.handle_suspect import handle_suspect
from spendings_tracker.app.harvest_month import harvest_month
from spendings_tracker.app.resume import resume
from spendings_tracker.app.save_monthly_close import SaveResult, save_monthly_close
from spendings_tracker.domain.draft import (
    HandleChoice,
    default_currency_totals,
    is_suspect,
    make_draft_line,
    other_currency_lines,
)
from spendings_tracker.ports.closer_ui import BotReply
from spendings_tracker.ports.harvest import HarvestPort
from spendings_tracker.ports.model import ModelPort
from spendings_tracker.ports.persistence import (
    PersistencePort,
    Settings,
    StoredDraft,
    StoredDraftLine,
)

PROPOSED_CATEGORIES = ["Groceries", "Transport"]
AUTH_MESSAGE = "You cannot use this bot."
HANDLE_ACTIONS = (
    "Enter amount",
    "Assign category",
    "Confirm Uncategorized",
    "Leave other currency listed",
    "Exclude from the close",
)
HANDLE_LABELS = {
    "Enter amount": HandleChoice.ENTER_AMOUNT,
    "Assign category": HandleChoice.ASSIGN_CATEGORY,
    "Confirm Uncategorized": HandleChoice.CONFIRM_UNCATEGORIZED,
    "Leave other currency listed": HandleChoice.LEAVE_OTHER_CURRENCY,
    "Exclude from the close": HandleChoice.EXCLUDE,
}
HARVEST_SCREENS = {
    "harvest.month_not_obtained": "SCR-03",
    "harvest.incomplete_month": "SCR-02",
    "harvest.draft_in_progress": "SCR-04",
    "harvest.egress_blocked": "SCR-02",
}


class TelegramBot:
    def __init__(
        self,
        persistence: PersistencePort,
        harvest: HarvestPort,
        model: ModelPort,
        *,
        now: datetime | None = None,
    ) -> None:
        self._persistence = persistence
        self._harvest = harvest
        self._model = model
        self._now = now
        self._pending_currency: dict[str, str] = {}
        self._pending_change: set[str] = set()
        self._pending_line: dict[str, str] = {}
        self._pending_assign: set[str] = set()
        self._pending_amount: set[str] = set()

    def _clear_follow_ups(self, user_id: str) -> None:
        self._pending_amount.discard(user_id)
        self._pending_assign.discard(user_id)

    def handle_group(self, user_id: str, chat_id: str, text: str) -> BotReply | None:
        return None

    def handle_private(self, user_id: str, chat_id: str, text: str) -> BotReply | None:
        settings = self._persistence.load_settings()
        if settings is not None and user_id != settings.closer_identity:
            return BotReply(
                chat_id=chat_id,
                text=AUTH_MESSAGE,
                screen="SCR-07",
                code="auth.not_closer",
            )
        stripped = text.strip()
        if stripped.startswith("/close"):
            return self._close(user_id, chat_id, stripped)
        if stripped.startswith("/save"):
            return self._save(chat_id)
        label = _bracket_label(stripped)
        if label is not None and label.startswith("Handle:"):
            shop = label.removeprefix("Handle:").strip()
            return self._pick_suspect(user_id, chat_id, shop)
        if label is not None and label in HANDLE_LABELS:
            return self._apply_choice(user_id, chat_id, HANDLE_LABELS[label])
        if label is not None and user_id in self._pending_assign:
            return self._assign_named_category(user_id, chat_id, label)
        if user_id in self._pending_amount:
            extra = label if label is not None else stripped
            return self._submit_amount(user_id, chat_id, extra)
        if stripped.startswith("handle "):
            return self._handle(user_id, chat_id, stripped)
        if settings is None:
            return self._first_run(user_id, chat_id, stripped)
        return self._resume_or_ready(chat_id, settings)

    def _close(self, user_id: str, chat_id: str, text: str) -> BotReply:
        try:
            settings = require_first_run(self._persistence)
        except AppError as err:
            if err.code == "first_run.still_required":
                return BotReply(
                    chat_id=chat_id,
                    text=err.message,
                    screen="SCR-01",
                    code=err.code,
                )
            raise
        parts = text.split()
        utc_month = parts[1] if len(parts) > 1 else ""
        try:
            result = harvest_month(
                self._persistence,
                self._harvest,
                self._model,
                utc_month,
                now=self._now,
            )
        except AppError as err:
            return BotReply(
                chat_id=chat_id,
                text=err.message,
                screen=HARVEST_SCREENS.get(err.code, "SCR-02"),
                code=err.code,
            )
        return self._draft_reply(chat_id, result.draft, settings)

    def _pick_suspect(self, user_id: str, chat_id: str, shop: str) -> BotReply:
        draft = self._persistence.load_draft()
        settings = self._persistence.load_settings()
        if draft is None or settings is None:
            err = catalog_error("save.no_draft")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-02", code=err.code
            )
        found = next(
            (
                line
                for line in draft.lines
                if line.shop_display == shop and not line.is_handled
            ),
            None,
        )
        if found is None:
            err = catalog_error("draft.line_not_found")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-05", code=err.code
            )
        self._pending_line[user_id] = found.id
        return self._scr05(chat_id, found.id)

    def _apply_choice(
        self,
        user_id: str,
        chat_id: str,
        choice: HandleChoice,
        *,
        extra: str | None = None,
    ) -> BotReply:
        line_id = self._pending_line.get(user_id, "")
        if choice is HandleChoice.ASSIGN_CATEGORY and extra is None:
            self._pending_amount.discard(user_id)
            self._pending_assign.add(user_id)
            return self._scr05_assign(chat_id, line_id)
        if choice is HandleChoice.ENTER_AMOUNT and extra is None:
            self._pending_assign.discard(user_id)
            self._pending_amount.add(user_id)
            return self._scr05_amount(chat_id, line_id)
        self._clear_follow_ups(user_id)
        return self._run_handle(user_id, chat_id, line_id, choice, extra)

    def _assign_named_category(
        self, user_id: str, chat_id: str, name: str
    ) -> BotReply:
        settings = self._persistence.load_settings()
        if settings is None:
            err = catalog_error("save.no_draft")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-02", code=err.code
            )
        found = next(
            (category for category in settings.categories if category.name == name),
            None,
        )
        if found is None:
            err = catalog_error("handle.unknown_category")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-05", code=err.code
            )
        self._pending_assign.discard(user_id)
        line_id = self._pending_line.get(user_id, "")
        return self._run_handle(
            user_id, chat_id, line_id, HandleChoice.ASSIGN_CATEGORY, found.id
        )

    def _submit_amount(self, user_id: str, chat_id: str, extra: str) -> BotReply:
        line_id = self._pending_line.get(user_id, "")
        reply = self._run_handle(
            user_id, chat_id, line_id, HandleChoice.ENTER_AMOUNT, extra
        )
        if reply.code != "handle.invalid_amount":
            self._clear_follow_ups(user_id)
        return reply

    def _scr05_amount(self, chat_id: str, line_id: str) -> BotReply:
        draft = self._persistence.load_draft()
        settings = self._persistence.load_settings()
        if draft is None or settings is None:
            err = catalog_error("save.no_draft")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-02", code=err.code
            )
        found = next((line for line in draft.lines if line.id == line_id), None)
        if found is None:
            err = catalog_error("draft.line_not_found")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-05", code=err.code
            )
        example = found.amount or "9.50"
        return BotReply(
            chat_id=chat_id,
            text=(
                "Enter the amount\n\n"
                f"Shop: {found.shop_display}\n"
                f"  [ {example} ]\n"
                "Type the amount."
            ),
            screen="SCR-05",
        )

    def _scr05_assign(self, chat_id: str, line_id: str) -> BotReply:
        draft = self._persistence.load_draft()
        settings = self._persistence.load_settings()
        if draft is None or settings is None:
            err = catalog_error("save.no_draft")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-02", code=err.code
            )
        found = next((line for line in draft.lines if line.id == line_id), None)
        if found is None:
            err = catalog_error("draft.line_not_found")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-05", code=err.code
            )
        picks = "\n".join(
            f"  [ {category.name} ]" for category in settings.categories
        )
        return BotReply(
            chat_id=chat_id,
            text=(
                "Assign a confirmed category\n\n"
                f"Shop: {found.shop_display}\n"
                f"{picks}\n"
                "Uncategorized is not on this list."
            ),
            screen="SCR-05",
        )

    def _run_handle(
        self,
        user_id: str,
        chat_id: str,
        line_id: str,
        choice: HandleChoice,
        extra: str | None,
    ) -> BotReply:
        amount = extra if choice is HandleChoice.ENTER_AMOUNT else None
        category_id = extra if choice is HandleChoice.ASSIGN_CATEGORY else None
        try:
            handle_suspect(
                self._persistence,
                closer_identity=user_id,
                draft_line_id=line_id,
                choice=choice,
                amount=amount,
                category_id=category_id,
            )
        except AppError as err:
            if err.code != "handle.invalid_amount":
                self._clear_follow_ups(user_id)
            screen = "SCR-02" if err.code == "save.no_draft" else "SCR-05"
            return BotReply(
                chat_id=chat_id, text=err.message, screen=screen, code=err.code
            )
        self._clear_follow_ups(user_id)
        settings = self._persistence.load_settings()
        draft = self._persistence.load_draft()
        if settings is None or draft is None:
            currency = settings.default_currency if settings else "EUR"
            return self._ready(chat_id, currency)
        return self._draft_reply(chat_id, draft, settings)

    def _handle(self, user_id: str, chat_id: str, text: str) -> BotReply:
        parts = text.split()
        line_id = parts[1] if len(parts) > 1 else ""
        choice_text = parts[2] if len(parts) > 2 else ""
        extra = parts[3] if len(parts) > 3 else None
        if line_id:
            self._pending_line[user_id] = line_id
        if not choice_text:
            return self._scr05(chat_id, line_id)
        try:
            choice = HandleChoice(choice_text)
        except ValueError:
            err = catalog_error("handle.unknown_choice")
            return BotReply(
                chat_id=chat_id,
                text=err.message,
                screen="SCR-05",
                code=err.code,
            )
        return self._apply_choice(user_id, chat_id, choice, extra=extra)

    def _save(self, chat_id: str) -> BotReply:
        settings = self._persistence.load_settings()
        try:
            result = save_monthly_close(self._persistence)
        except AppError as err:
            if err.code == "save.no_draft":
                return BotReply(
                    chat_id=chat_id, text=err.message, screen="SCR-02", code=err.code
                )
            draft = self._persistence.load_draft()
            if (
                err.code == "save.unhandled_suspect"
                and settings is not None
                and draft is not None
            ):
                body = self._draft_reply(chat_id, draft, settings)
                return BotReply(
                    chat_id=chat_id,
                    text=f"{err.message}\n\n{body.text}",
                    screen="SCR-04",
                    code=err.code,
                )
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-04", code=err.code
            )
        return self._save_reply(chat_id, result, settings)

    def _first_run(self, user_id: str, chat_id: str, text: str) -> BotReply:
        label = _bracket_label(text)
        if label is not None and label.startswith("Keep "):
            chosen = label.removeprefix("Keep ").strip().upper()
            self._pending_change.discard(user_id)
            self._pending_currency[user_id] = chosen or "EUR"
            return self._first_run_prompt(chat_id, self._pending_currency[user_id])
        if label is not None and label.startswith("Change"):
            self._pending_change.add(user_id)
            return self._first_run_prompt(
                chat_id, self._pending_currency.get(user_id, "EUR")
            )
        if label == "Confirm list":
            return self._confirm_first_run(user_id, chat_id, list(PROPOSED_CATEGORIES))
        if user_id in self._pending_change:
            chosen = text.strip().upper()
            self._pending_change.discard(user_id)
            if chosen:
                self._pending_currency[user_id] = chosen
            return self._first_run_prompt(
                chat_id, self._pending_currency.get(user_id, "EUR")
            )
        lowered = text.lower()
        if lowered in {"keep", "keep eur"}:
            self._pending_currency[user_id] = "EUR"
            return self._first_run_prompt(chat_id, "EUR")
        if lowered.startswith("change"):
            parts = text.split()
            chosen = parts[1].upper() if len(parts) > 1 else ""
            if chosen:
                self._pending_currency[user_id] = chosen
            return self._first_run_prompt(
                chat_id, self._pending_currency.get(user_id, chosen or "EUR")
            )
        if text.startswith("confirm"):
            remainder = text[len("confirm") :]
            names = [
                part.strip() for part in remainder.split(",") if part.strip()
            ]
            return self._confirm_first_run(user_id, chat_id, names)
        return self._first_run_prompt(
            chat_id, self._pending_currency.get(user_id, "EUR")
        )

    def _confirm_first_run(
        self, user_id: str, chat_id: str, names: list[str]
    ) -> BotReply:
        currency = self._pending_currency.get(user_id, "EUR")
        try:
            settings = complete_first_run(
                self._persistence,
                closer_identity=user_id,
                default_currency=currency,
                category_names=names,
            )
        except AppError as err:
            return BotReply(
                chat_id=chat_id,
                text=err.message,
                screen="SCR-01",
                code=err.code,
            )
        return self._ready(chat_id, settings.default_currency)

    def _first_run_prompt(self, chat_id: str, currency: str) -> BotReply:
        proposed = "\n".join(f" • {name}" for name in PROPOSED_CATEGORIES)
        return BotReply(
            chat_id=chat_id,
            text=(
                "First-run setup\n"
                f"Default currency: {currency}\n"
                "[ Keep EUR ]  [ Change… ]\n"
                f"Categories:\n{proposed}\n"
                "[ Confirm list ]"
            ),
            screen="SCR-01",
        )

    def _resume_or_ready(self, chat_id: str, settings: Settings) -> BotReply:
        state = resume(self._persistence)
        if state.kind == "draft" and state.draft is not None:
            return self._draft_reply(chat_id, state.draft, settings)
        if state.kind == "first_run":
            return self._first_run_prompt(chat_id, "EUR")
        return self._ready(chat_id, settings.default_currency)

    def _ready(self, chat_id: str, default_currency: str) -> BotReply:
        return BotReply(
            chat_id=chat_id,
            text=(
                "Ready\n"
                f"Default currency: {default_currency}\n"
                "Category list: frozen\n"
                "Monthly closes can start."
            ),
            screen="SCR-02",
        )

    def _scr05(self, chat_id: str, line_id: str) -> BotReply:
        draft = self._persistence.load_draft()
        settings = self._persistence.load_settings()
        if draft is None or settings is None:
            err = catalog_error("save.no_draft")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-02", code=err.code
            )
        found = next((line for line in draft.lines if line.id == line_id), None)
        if found is None:
            err = catalog_error("draft.line_not_found")
            return BotReply(
                chat_id=chat_id, text=err.message, screen="SCR-05", code=err.code
            )
        names = {category.id: category.name for category in settings.categories}
        actions = "\n".join(f"[ {label} ]" for label in HANDLE_ACTIONS)
        return BotReply(
            chat_id=chat_id,
            text=(
                "Handle suspect\n\n"
                f"{_line_label(found, names)}\n\n"
                f"{actions}"
            ),
            screen="SCR-05",
        )

    def _draft_reply(
        self,
        chat_id: str,
        draft: StoredDraft,
        settings: Settings,
    ) -> BotReply:
        names = {category.id: category.name for category in settings.categories}
        currency = settings.default_currency
        if not draft.lines:
            return BotReply(
                chat_id=chat_id,
                text=(
                    f"Private draft  {draft.utc_month}\n\n"
                    "No spend-looking lines.\n"
                    f"Totals ({currency}): empty\n"
                    "Suspects: none\n"
                    "Egress: none\n\n"
                    "You may /save and accept empty totals"
                ),
                screen="SCR-04",
            )
        domain_lines = [
            make_draft_line(
                amount=line.amount,
                currency=line.currency,
                category_id=line.category_id,
                is_excluded=line.is_excluded,
                is_handled=line.is_handled,
            )
            for line in draft.lines
        ]
        totals = default_currency_totals(domain_lines, default_currency=currency)
        others = other_currency_lines(domain_lines, default_currency=currency)
        suspects = [
            line
            for line, domain in zip(draft.lines, domain_lines, strict=True)
            if is_suspect(domain, default_currency=currency) and not line.is_handled
        ]
        pick_block = (
            "\n".join(f"  [ Handle: {line.shop_display} ]" for line in suspects)
            if suspects
            else ""
        )
        line_block = "\n".join(
            f"  {_line_label(line, names)}" for line in draft.lines
        )
        total_block = (
            "\n".join(
                f"  {names.get(category_id) or 'Uncategorized'}   {amount}"
                for category_id, amount in totals.items()
            )
            or "  (none)"
        )
        other_block = (
            "\n".join(
                f"  {line.currency} {line.amount or '—'}"
                for line in others
            )
            or "  (none)"
        )
        egress = draft.egress_lines
        egress_block = (
            "\n".join(f"  • {row.line_text}" for row in egress) or "  (none)"
        )
        return BotReply(
            chat_id=chat_id,
            text=(
                f"Private draft  {draft.utc_month}\n\n"
                f"Lines\n{line_block}\n\n"
                f"Totals ({currency} only)\n{total_block}\n\n"
                f"Other currencies (listed, not mixed)\n{other_block}\n\n"
                f"Suspects remaining: {len(suspects)}\n"
                f"{pick_block}\n\n"
                f"Egress (every line that left)\n{egress_block}"
            ),
            screen="SCR-04",
        )

    def _save_reply(
        self, chat_id: str, result: SaveResult, settings: Settings | None
    ) -> BotReply:
        names = (
            {category.id: category.name for category in settings.categories}
            if settings is not None
            else {}
        )
        currency = result.close.default_currency
        if result.totals:
            totals_block = "\n".join(
                f"  {names.get(category_id) or 'Uncategorized'}   {amount}"
                for category_id, amount in result.totals.items()
            )
        else:
            totals_block = "  (empty)"
        others = [
            line
            for line in result.close.lines
            if line.currency != currency
        ]
        other_note = (
            "Other currencies listed, not mixed."
            if others
            else "Other currencies listed, not mixed."
        )
        replaced = (
            "This save replaced the previous close for that month.\n"
            if result.replaced
            else ""
        )
        return BotReply(
            chat_id=chat_id,
            text=(
                "Monthly close saved\n\n"
                f"{result.close.utc_month} recorded.\n"
                f"{replaced}"
                f"Save accepted the {currency} totals:\n"
                f"{totals_block}\n"
                f"{other_note}\n\n"
                "Ready."
            ),
            screen="SCR-06",
        )


def _bracket_label(text: str) -> str | None:
    stripped = text.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped[1:-1].strip()
    return None


def _line_label(line: StoredDraftLine, names: dict[str, str]) -> str:
    amount = line.amount or "—"
    category = names.get(line.category_id) if line.category_id else "Uncategorized"
    return f"{line.shop_display}  {amount} {line.currency}  {category}"
