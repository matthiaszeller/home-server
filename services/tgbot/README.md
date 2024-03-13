
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
The interaction between these components is facilitated through an asyncio Queue, 
enabling message passing and command execution between the bot and the server without blocking the event loop.

### Telegram Bot

The bot component is built using the python-telegram-bot library, adapted for asyncio compatibility. 
It listens for user commands, processes incoming messages, and can send responses based on commands received through 
the API server. The bot's main function, run, manages the addition of command handlers, error handling, 
and message processing from an asyncio Queue, ensuring seamless operation within an asyncio-driven environment.

### API Server

The API server is developed with Quart, an asyncio-compatible microframework similar to Flask. It exposes an endpoint /enqueue_command that accepts POST requests. These requests are intended to carry commands to be enqueued into the shared asyncio Queue, allowing for asynchronous communication between the external world (e.g., a web frontend) and the bot component.

### Message Queue

At the heart of the interaction between the bot and the API server lies an asyncio Queue (message_queue). This queue enables the decoupling of the bot's operations from the API server, allowing for asynchronous message passing and command execution. The API server enqueues commands received from HTTP requests, and the bot dequeues these commands for processing, facilitating a reactive system that can respond to external triggers without interrupting its core loop.


## TODOs

- [x] SSL API
- [ ] API authentication
- [ ] dispatch telegram commands to other services
- [ ] get response in message queue
