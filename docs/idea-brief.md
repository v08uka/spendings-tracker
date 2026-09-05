---
status: Draft
owner: Dell
updated_at: 2026-09-05
depth: medium
---

# Idea brief — monthly-spend-close

## 1. Raw idea

I want to create a Telegram bot. This can be run locally on this computer for now. My family has a Telegram group. A member posts a message about expenses, for example "Products Spar /n 1500" - which means that 1500 default currency was spent on Products. When a report for a specific month is requested the bot should be able to: read messages for the specific month; generate a context for the LLM API for a monthly report on which category, how much was spent (Categories are still primitive); correctly handling the currency (if it is not specified - take the default currency); send a request to the LLM API (for now I don't want to be tied to a specific LMM, so I would like it to be an abstraction over: OpenAI (some cost effective) & Monosnap (Kimi 2.7)); process the response and send me a response; save/edit state/settings e.g. prefered categories, default currency, output currency/currencies; save the report (by month) for Future comparsion. On bot initialization: setup currencies: default and report output; setup default categories or allow LLM chose them; optionally set the Store/Place Name - category map and save it (for more deterministic mapping). Bot do not have to be running always - I can run shell commands, boot bot, genegate report then kill the containers (extept db-state), and do it again next month.

## 2. Problem

The family Telegram group already mentions shops and amounts, but that chat is not a month you can close. Once a month the person who cares must turn a noisy mix of real spends, jokes, and split-cost asides into a picture of “which bucket, how much” they are willing to believe. Re-reading the month by hand is the current fallback; a pretty total with no line list would not be believed. There is no external deadline — each passing month is another unread close sitting in the group.

## 3. Users

**Closer** — the idea’s author. Runs the bot on this computer when they want a month, reviews every extracted line, corrects or drops, then keeps the saved month and the settings (category list, default currency, optional shop→bucket map). Success is one month they trust, not a family product.

**Family posters** — people already dropping shop and amount mentions in the group. They are a data source, not operators. They do not need to open the bot, agree a format, or see the report.

## 4. Why now

No contract, launch date, or incident was named. The live trigger is that spend-shaped lines are already appearing in the group, so the raw material exists today. Waiting costs another unsummarized month, not a closing window. “It would be useful” is the honest urgency.

## 5. Out of scope

- Treating the family as product users, or charging other families — the closer is the only operator.
- Changing family habit, “only the closer logs,” or “forward spends to the bot” — the source is harvest of what the group already writes.
- Totals-only reports with no line list — a close is believed only after audit.
- Sending a whole month of group chat to an outside language-model service — only spend-looking lines may leave the machine.
- Converting amounts into one output money, or multi-currency grand totals — one default currency; other currencies stay as-is and are flagged in the audit.
- Letting the model invent category names each run — the closer owns a short fixed list.
- A file-only close with no bot conversation — rejected; Telegram is both archive and how the closer asks for the month.
- Receipt photos, voice messages, reports as pictures, hosting on someone else’s computers.
- Comparing saved months, yearly reports, scheduled recurring spends (rent, tuition, subscriptions), and a spending advisor (gaps, overspend, habits, investments).
- An always-on bot — start it for a close, then stop it; keep settings and saved months.

## 6. Risks

- **Weakest spot:** the audit can take longer than scrolling the group. The bot only wins if checking the draft is faster than re-reading chat. Assumes the draft is a shortcut; false if harvest is so messy that every line needs a trip back to the original message.
- Assumes the group already posts shop-and-amount lines often enough to close a month; false if that habit is thinner than it feels, or a quiet month looks like “we spent nothing.”
- Assumes a local first-pass can spot spend-looking lines without the rest of the conversation; false if jokes, “we split it,” and “about 200” are indistinguishable from real spends until you have the thread.
- Assumes the bot can re-read last month’s group history after it was stopped; false if starting cold cannot see that month — then the whole on-demand close fails.
- Assumes the closer will actually finish the audit before trusting totals; false if they glance and move on — one joke counted as a purchase trains them to ignore the report.
- Assumes an outside language-model service is worth the leak of even the filtered lines; false if the family would not accept those lines leaving the house, or if switching vendors later still means history already went to the first one.

## 7. Recommendation

Build an on-demand Telegram monthly close for the closer only. They start the bot when they want a month; it reads that month from the family group, keeps likely spend lines on the machine, sends only those lines to a language-model service (vendor not locked), files each line into the closer’s fixed category list (or Uncategorized), and sends the closer a private draft. They fix or drop lines, then the month is saved and the bot can be stopped. One default currency; other currencies are listed, not converted. An optional shop→category map grows from corrections. That is the whole first product — not a family app, not a converter, not an advisor.

## 8. Open questions

- What is the default currency, and what are the first category names on the fixed list? — owner
- If the bot was off all month, can it still read that month’s group history when started? — owner (must be true or the on-demand shape breaks)
- Start the shop→category map empty, or seed a few known shops at first setup? — owner
- How incomplete can a harvested month be and still count as a trusted close (missing cash vs. wrong lines)? — owner
