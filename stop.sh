#!/bin/bash
PID=$(lsof -ti :8100)
if [ -z "$PID" ]; then
  echo "Builder's OS is not running on port 8100."
else
  kill $PID
  echo "Stopped Builder's OS (PID $PID)."
fi
