"""Long-poll the Bot API until SIGINT/SIGTERM. No webhook."""

from __future__ import annotations

import signal
from collections.abc import Callable
from typing import Any

from spendings_tracker.infra.telegram_bot import TelegramBot


def telegram_long_poll(
    bot: TelegramBot, token: str, stop: Any | None = None
) -> None:
    from telegram.ext import Application, MessageHandler, filters

    application = Application.builder().token(token).build()

    async def on_text(update: Any, context: Any) -> None:
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None:
            return
        text = message.text or ""
        user_id = str(user.id)
        chat_id = str(chat.id)
        if chat.type != "private":
            bot.handle_group(user_id, chat_id, text)
            return
        reply = bot.handle_private(user_id, chat_id, text)
        if reply is not None:
            await message.reply_text(reply.text)

    application.add_handler(MessageHandler(filters.TEXT, on_text))
    stop_signals: tuple[signal.Signals, ...] | None
    if stop is not None:
        stop_signals = ()
    else:
        stop_signals = (signal.SIGINT, signal.SIGTERM)
    application.run_polling(stop_signals=stop_signals, close_loop=True)


PollFn = Callable[[TelegramBot, str, Any | None], None]


def run_until_stop(
    bot: TelegramBot,
    token: str,
    *,
    poll: PollFn | None = None,
    stop: Any | None = None,
) -> None:
    runner = poll if poll is not None else telegram_long_poll
    runner(bot, token, stop)
