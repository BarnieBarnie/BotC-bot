#! /usr/bin/env bash

cd /home/ubuntu
git clone https://github.com/BarnieBarnie/BotC-bot.git
sudo apt update && sudo apt install python3.10-venv -y
cd BotC-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mv /home/ubuntu/token.txt /home/ubuntu/BotC-bot/token.txt
python3 main.py