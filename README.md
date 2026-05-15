# Kitchen helper bot

Telegram bot for storing recipes and generating PDF recipe cards.

The bot allows users to:
 - create recipes
 - manage ingredients
 - edit recipes
 - generate PDF files from stored data

# Stack

 - Python 3.12
 - Aiogram 3
 - PostgreSQL
 - SQLAlchemy
 - Alembic
 - AsyncIO
 - ReportLab

# Features

 - Create recipes
 - Add/Edit/Delete ingredients
 - Delete recipes
 - Generate PDF recipe cards
 - Logging system
 - Async database interaction

# Project structure

handlers/     - Telegram handlers
services/     - Business logic
repositories/ - Database queries
keyboards/    - Telegram keyboards
utils/        - Helpers and formatters
db/           - Database models and setup
