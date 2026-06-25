# Murdermotel WebSocket API - TODO

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
