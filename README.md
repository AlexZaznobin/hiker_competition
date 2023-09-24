# Competition Plan Bot
## Introduction
This bot helps users to generate a competition plan. It provides a detailed schedule for X teams with Y available tasks and a specific number of Z tasks that each team should go through. The bot can generate a schedule in the form of an Excel table and supports multiple languages, such as English and Russian.

## Table of Contents
Features
Setup & Installation
Usage
Development

## Features
Multilingual Support: Supports both English and Russian.
Dynamic Scheduling: Generates schedule based on the provided input.
Error Handling: Can handle incorrect inputs gracefully.
Logging: Keeps detailed logs of user interactions.
FastAPI Integration: Has a foundation for potential future web endpoints.

## Setup & Installation 
Clone the Repository

Get a local copy of the repository using:

bash
Copy code
git clone <repository_link>
Install Dependencies

Install all required libraries:

bash
Copy code
pip install -r requirements.txt
Configuration

Update the config.json with necessary details:

json
Copy code
{
    "telegram": "YOUR_BOT_TOKEN",
    "link": "DEVELOPER_LINK"
}
Replace YOUR_BOT_TOKEN with the bot token from Telegram BotFather.
Replace DEVELOPER_LINK with the contact link for the developer.
Run the Bot

Execute the following command:

bash
Copy code
python hiker_competition.py


## Usage
Initiate the bot with the /start command.
Select the desired language.
Follow the prompts and input the required details.
The bot will generate and provide the schedule in an Excel format.

## Development 
The bot is crafted using the aiogram library for Telegram bot interactions, integrated with FastAPI for potential web endpoints. The bot utilizes pandas for data operations and Excel sheet creation. It maintains comprehensive logs of every user interaction, including user details and messages.
