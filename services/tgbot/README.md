
# Telegram behind REST API

## Getting Started

Need to specify following secrets:

- `config/secrets/allowed_user.txt`
- `config/secrets/bot_api.txt`
- `config/secrets/certificate.pem`
- `config/secrets/key.pem`

To generate self-signed certificate:
```shell
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem
```


## Software Architecture

### Overview

This application integrates an asynchronous Telegram bot with an asynchronous API server using Python's asyncio library.
The software architecture is designed around the asyncio event loop,
allowing for concurrent execution of the bot and the API server within the same application.
The interaction between these components is facilitated through bi-directional communication using asyncio Queues,
enabling both command execution and response handling between the bot and the server without blocking the event loop.


### Components

#### Telegram Bot

The bot component is built using the `python-telegram-bot` library, adapted for asyncio compatibility.
It listens for user commands, processes incoming messages, and can send responses based on commands received through
the API server. The bot's main function `TelegramBot.run`, manages the addition of command handlers, error handling,
and message processing, and responding to commands via an asyncio Queue,
ensuring seamless operation within an asyncio-driven environment.

#### API Server

The API server is developed with Quart, an asyncio-compatible microframework similar to Flask.
It exposes an endpoint `/enqueue_command` that accepts POST requests.
These requests are intended to carry commands to be enqueued into the shared asyncio Queue,
allowing for asynchronous communication between the external world (e.g., a web frontend) and the bot component.

#### Message Queue

At the heart of the interaction between the bot and the API server lies an asyncio Queue (message_queue).
This queue enables the decoupling of the bot's operations from the API server,
allowing for asynchronous message passing and command execution.
The API server enqueues commands received from HTTP requests, and the bot dequeues these commands for processing,
facilitating a reactive system that can respond to external triggers without interrupting its core loop.

#### Response Handling Mechanism

Upon enqueuing a command, the API server packs the command data with a `asyncio.Future` object,
who is waited to get the response from the bot.

### Interaction

#### Commands and Tasks

Definitions:
- **Command**: A message sent by a user to the bot, containing a specific instruction or request. See telegram bot commands (https://core.telegram.org/bots#commands).
- **Task**: an API-requested operation that the bot should perform, such as sending a message to a user or updating a chat.

## Security

### Security Overview

1. **For API Services**:
    * **Authentication**: services calling the API has a unique token to authenticate themselves.
    * **Authorization**: once a service is authenticated, it can only access the resources it is authorized to access.
2. **For Telegram Users**:
    * **User Identification**: Telegram users are identified by their unique chat ID provided by the Telegram API.
      There's no need for additional authentication as their telegram session handles it.
    * **Command Permissions**: Similar to services, we map Telegram commands to roles or directly to user IDs for authorization.

### Access Control

* **Service-based API Access**:
   * Services are authenticated using unique API keys.
   * Each service is assigned a role that determines its permissions, specifically which API endpoints it can access.
   * Permissions are defined in a permissions.yaml file, mapping roles to sets of accessible API endpoints.
   * API keys and their corresponding roles are securely stored and managed in an .env file, separate from the application codebase to enhance security.

* **Telegram User Command Access**:
  * Telegram users are identified by their Telegram user IDs.
  * Similar to services, users are assigned roles that specify which Telegram commands they can execute.
  * Roles and command permissions for Telegram users are also defined in the permissions.yaml file.
  * User roles are mapped in the .env file, correlating Telegram user IDs with their respective roles.


## TODOs

- [x] SSL API
- [ ] API authentication
- [ ] dispatch telegram commands to other services
- [x] get response in message queue
