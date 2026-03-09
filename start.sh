#!/bin/bash
# Script de inicialização para Railway

cd backend
uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}