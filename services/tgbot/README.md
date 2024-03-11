
# Telegram behind REST API

## Getting Started

Need to specify following secrets:

- `config/secrets/allowed_user.txt`
- `config/secrets/bot_api.txt`

## Software Architecture

### Concurrent blocking bot and REST API server

Flask runs in a separate thread, while telegram bot runs on main thread. 
Reason is: flask is synchronous, telegram bot is async. It's easier to handle async in main thread.

