@echo off
echo Setting up AWS credentials...

set /p AWS_ACCESS_KEY_ID=Enter your AWS Access Key ID: 
set /p AWS_SECRET_ACCESS_KEY=Enter your AWS Secret Access Key: 
set /p AWS_DEFAULT_REGION=Enter your AWS Region (e.g., us-east-1): 

mkdir "%USERPROFILE%\.aws" 2>nul

(
echo [default]
echo aws_access_key_id=%AWS_ACCESS_KEY_ID%
echo aws_secret_access_key=%AWS_SECRET_ACCESS_KEY%
echo region=%AWS_DEFAULT_REGION%
) > "%USERPROFILE%\.aws\credentials"

echo AWS credentials have been set up in %USERPROFILE%\.aws\credentials
echo Please restart your terminal for changes to take effect.
pause
