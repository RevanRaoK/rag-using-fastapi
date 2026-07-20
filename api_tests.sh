#!/bin/bash

echo "Testing the root endpoint..."
curl http://127.0.0.1:8000/
echo -e "\n"

echo "Testing file upload..."
curl -X 'POST' \
  'http://127.0.0.1:8000/uploadfile/' \
  -F 'file=@hi.txt'
echo -e "\n"

echo "Testing the ask question endpoint..."
curl -X 'POST' \
  'http://127.0.0.1:8000/ask/' \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is the capital of France?"}'
echo -e "\n"
