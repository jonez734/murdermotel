# Murdermotel WebSocket API - TODO

## BED bearer token

- [ ] See `bed/TODO.md` "Bearer token" — adopt `bed.api.auth.AuthService` for BED-mode authentication and reconnect. Replaces per-game `auth` implementations. Murdermotel benefits strongly: long-lived investigation/investment sessions can reconnect mid-night without re-login.

## BED `Sink` integration with `bbsengine6.io` (cross-project)

- [ ] See `bbsengine6/TODO.md` "`bbsengine6.io` sink infrastructure
  for thin-client BED conversion" (Phases 0–5) — the
  `bbsengine6.io.sink.Sink` protocol, `set_io_sink` /
  `reset_io_sink` contextvar API, `bbsengine6.io.echo_render` and
  `mci.parse` / `mci.render` public functions, and the
  `MessageRouter` / `MessageRouterMixin` in
  `bbsengine6/net/router.py`.
- [ ] See `bed/TODO.md` "BED `Sink` integration with
  `bbsengine6.io`" — the `BEDSink` (per-connection adapter in
  `bed/sinks/bed_sink.py`) and the `on_connect_hook` installation
  point on the `WebSocketServer`. Murdermotel is the second primary
  driver of the `key_f2` session-level new-messages query (motel
  events channel) — see `bed/TODO.md` "`key_f2` — session-level
  new-messages query" for the per-game adoption.
- [ ] **No code change required for the murdermotel `MessageRouter`
  in v1.** The murdermotel can opt into `MessageRouterMixin` later
  (a one-line change to its class declaration:
  `class MessageRouter(MessageRouterMixin):`) to gain the session
  API. v1 ships without the mixin; the BED sink infrastructure
  works against the bare `murdermotel.api.handler.MessageRouter`.
- [ ] **Backward compat**: door mode (no `BEDSink` installed) uses
  the default `DefaultSink` behavior, which is the current
  `bbsengine6.io` behavior byte-for-byte. The
  `bbsengine6/tests/test_io_backward_compat.py` suite passes for
  the murdermotel door-mode pytest corpus.

## Overview

Create a WebSocket API for murdermotel using bbsengine6.services.session.

## Database

- [ ] **player_view.sql (NEW)** - Create `murdermotel.player` view with timezone-converted timestamps
  - Base table: `murdermotel.player`
  - Add `datelastplayedlocal`, `datecreatedlocal` (like casino/empyre views)

## Services

- [ ] **services/player.py (NEW)** - Player data service
  - `get_player(moniker)` - get player info from view
  - `create_player(moniker)` - create new player
  - `update_player(moniker, data)` - update player data
  - Uses view for SELECTs, table for INSERTs/UPDATEs

- [ ] **services/game.py (NEW)** - Game command handlers
  - [ ] **Movement**: `move(direction)` - U/D/N/S/E/W
  - [ ] **Combat**: `kill_target()` - attack target
  - [ ] **Items**: `take_item(item)`, `leave_item(item)`
  - [ ] **Info**: `player_info()`, `compass()`
  - [ ] **Social**: `read_news()`, `read_map()`, `leaderboard()`, `high_kills()`
  - [ ] **Game**: `help()`, `quit()`

  Each command returns available_actions for the next turn.

## API Handler

- [ ] **api/handler.py (NEW)**
  - [ ] `PlayerServiceHandler` - player profile/stats
  - [ ] `GameServiceHandler` - all game commands
  - [ ] `ChannelServiceHandler` - channel subscriptions
  - [ ] `MessageRouter` - route messages to services

### Message Types

- [ ] `player_profile` - Get player info
- [ ] `player_update` - Update player settings
- [ ] `move` - Move in direction (U/D/N/S/E/W)
- [ ] `kill_target` - Attack your target
- [ ] `take_item` - Pick up item from room
- [ ] `leave_item` - Drop item in room
- [ ] `compass` - Show available exits
- [ ] `player_info` - Show player stats
- [ ] `read_news` - Read motel newspaper
- [ ] `read_map` - Show motel maps
- [ ] `leaderboard` - Show high points
- [ ] `high_kills` - Show kill leaders
- [ ] `help` - Show available commands

### Channel Subscriptions

- [ ] `murdermotel:global` - Global chat
- [ ] `murdermotel:room:{roomid}` - Room-specific chat
- [ ] `member:{moniker}` - Direct messages (from bbsengine6)

## Integration

- [ ] Import `bbsengine6.services.session` for session management
- [ ] Use bbsengine6 net/transport.py for channel pub/sub
- [ ] Response format includes `module: "murdermotel"` field

## Dependencies

- [ ] bbsengine6.services.session
- [ ] bbsengine6.services.member (for member data)
- [ ] bbsengine6.net.transport (for channels)
- [ ] murdermotel.player table
- [ ] murdermotel.player view (to create)
