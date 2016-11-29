@echo off

for %%i in (*.json) do (
    py jsonfmt.py "%%~i"
)

