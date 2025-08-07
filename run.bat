@echo off

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Load .env variables
for /f "delims=" %%i in (.env) do set %%i

REM Start Flask
flask run

pause
