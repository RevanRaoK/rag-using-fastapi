@echo off
echo Testing the root endpoint...
curl http://127.0.0.1:8000/
echo.
echo.

echo Testing file upload...
curl -X POST "http://127.0.0.1:8000/uploadfile/" -F "file=@hi.txt"
echo.
echo.

echo Testing the ask question endpoint...
curl -X POST "http://127.0.0.1:8000/ask/" -H "Content-Type: application/json" -d "{\"question\": \"What is the capital of France?\"}"
echo.
echo.
pause
