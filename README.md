# SMS Chat

GroupMe-style SMS group chat. Users create/join groups via web or GraphQL API, and chat via SMS. Messages sent to the group are broadcast to all members via Twilio.

## Features

- Phone-based authentication with JWT
- Create, join, and leave groups
- Send messages via web UI, GraphQL, or SMS
- Inbound SMS routing (single group auto-select, or `#groupname` prefix for multi-group users)
- SMS broadcast to group members via Twilio

## Quick Start

```bash
# Install
pip install -r requirements.txt
cp .env.example .env  # edit with your settings

# Run
python manage.py migrate
python manage.py runserver
```

## URLs

- `http://localhost:8000/` - Web UI
- `http://localhost:8000/graphql/` - GraphQL Playground
- `/webhooks/twilio/inbound/` - Twilio SMS webhook
