@echo off
title ErdemMusic
color a
pip install -U youtube_dl
pip install -U discord.py[voice]
cls
:a
py bot.py
goto a