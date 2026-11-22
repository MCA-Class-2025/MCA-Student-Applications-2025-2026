@echo off
where ollama >nul 2>nul
if errorlevel 1 (
 echo Ollama is not installed. Install it from https://ollama.com/download/windows
 pause
 exit /b 1
)
ollama pull qwen2.5:1.5b
echo Local LLM ready. FundFlow can still run without Ollama using its offline fallback.
pause
