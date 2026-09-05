# spendings-tracker

Conventions from `docs/architecture-map.md` and ADRs 0001–0003. Features build into this skeleton; do not re-litigate the stack here.

## Stack

- Python 3.12, one process, Compose (`uv sync` / `pytest` / `ruff check .`).
- No in-repo frontend. Telegram is the closer’s UI — specify bot commands, not pages.
- SQLite file on a named Compose volume. Schema changes go through Alembic (`alembic upgrade head` / `alembic downgrade base`).
- IDs for persisted rows are time-sortable ULIDs.

## Layout

One package, hexagonal layers, no second bounded context yet:

| Layer | Path | Rule |
|---|---|---|
| domain | `src/spendings_tracker/domain` | Rules only. No Telegram, no vendor SDK, no DB driver. |
| app | `src/spendings_tracker/app` | Use cases. One error type: `AppError`. Adapters translate vendor/Telegram failures into it. |
| ports | `src/spendings_tracker/ports` | Interfaces. New chat or model vendor is a port + infra adapter. |
| infra | `src/spendings_tracker/infra` | Adapters. Domain and app do not import this package. |

Wire at `src/spendings_tracker/__main__.py`: construct infra adapters and inject them at ports.

## Where new work goes

- New use case → `src/spendings_tracker/app`.
- New Telegram or language-model vendor → `ports` + `infra`, never `domain`.
- New persisted concept → Alembic migration + persistence adapter.
- Tests: `pytest`. Unit tests live at domain/app with fakes at ports. One smoke test that the app boots.

## Constraints

- Local, on-demand: start for a close, then stop. State must survive.
- Only spend-looking lines may leave the machine for a language-model service.
- One writer on the SQLite file.
- In-process calls only — no second service.
