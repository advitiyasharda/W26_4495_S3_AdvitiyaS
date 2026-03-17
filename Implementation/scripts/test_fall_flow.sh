#!/bin/bash
# Test flow for LSTM fall detection
# Run each command in a separate terminal.

echo "Terminal 1 — Backend:"
echo "  cd Implementation && python3.11 main.py"
echo ""
echo "Terminal 2 — LSTM Fall Detector:"
echo "  cd Implementation && python3.11 scripts/fall_detection_camera.py --lstm"
echo ""
echo "Terminal 3 — Frontend:"
echo "  cd Implementation/frontend && npm run dev"
echo ""
echo "Then open http://localhost:3000/falls"
echo ""
echo "Verify:"
echo "  - Falls appear when LSTM detects them"
echo "  - Confidence bar updates based on latest fall"
echo "  - Move too close → yellow visibility banner (no repeated false falls)"
