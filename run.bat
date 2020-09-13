@echo off
title ErdemMusic
color a
pip install -U discord.py[voice]
pip install -U youtube.dl
pip install -U pip
pip install -U textblob
pip install -U aiohttp
pip install -U asyncio
cls
:a
py bot.py
goto a