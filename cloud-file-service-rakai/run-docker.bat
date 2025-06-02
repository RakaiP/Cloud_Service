@echo off
ECHO ===== RUNNING CLOUD SERVICES IN DOCKER =====

ECHO Stopping any existing containers...
docker-compose down

ECHO Building containers...
docker-compose build

ECHO Starting containers...
docker-compose up

ECHO Done!
