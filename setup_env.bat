@echo off
set CRED_PATH=%USERPROFILE%\.aws\credentials

if not exist "%CRED_PATH%" goto SETUP_CREDS
goto LOAD_CREDS

:LOAD_CREDS
echo AWS credentials file exists at %CRED_PATH%, loading credentials...
goto SETUP_VENV

:SETUP_CREDS
echo Setting up AWS credentials...
set /p AWS_ACCESS_KEY_ID=Enter your AWS Access Key ID: 
set /p AWS_SECRET_ACCESS_KEY=Enter your AWS Secret Access Key: 
set /p AWS_DEFAULT_REGION=Enter your AWS Region (e.g., us-east-1): 
mkdir "%USERPROFILE%\.aws" 2>nul
echo [default] > "%CRED_PATH%"
echo aws_access_key_id=%AWS_ACCESS_KEY_ID% >> "%CRED_PATH%"
echo aws_secret_access_key=%AWS_SECRET_ACCESS_KEY% >> "%CRED_PATH%"
echo region=%AWS_DEFAULT_REGION% >> "%CRED_PATH%"
echo AWS credentials have been set up in %CRED_PATH%
goto SETUP_VENV

:SETUP_VENV
echo Setting up Python virtual environment...
if exist "venv" goto VENV_EXISTS
goto CREATE_VENV

:VENV_EXISTS
echo Virtual environment already exists.
goto ACTIVATE_VENV

:CREATE_VENV
python -m venv venv
echo Virtual environment created.
goto ACTIVATE_VENV

:ACTIVATE_VENV
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing required packages...
pip install -r requirements.txt
echo Environment setup complete!
echo.
echo To start the ProdPal Web Chat, run:
echo python app.py
echo.
echo Then open your browser and navigate to:
echo http://localhost:5000
echo.
pause
