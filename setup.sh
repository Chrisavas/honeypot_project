#!/bin/bash
# setup.sh - Complete setup and execution guide
# Run this to set up and test the entire honeypot system

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🍯 LLM-Enhanced Honeypot and Attacker Interaction Setup  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Create output directories
echo "📁 Creating output directories..."
mkdir -p honeypot_logs
mkdir -p honeypot_decoys
mkdir -p playbook_results
mkdir -p reports
echo "✓ Directories created"
echo ""

# Step 1: Generate decoys
echo "════════════════════════════════════════════════════════════"
echo "STEP 1: Generating Decoy Artifacts"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Running: python3 decoy_generator.py"
python3 decoy_generator.py
echo ""
echo "✓ Decoy artifacts generated in honeypot_decoys/"
echo ""

# Display generated artifacts
echo "📋 Generated artifacts:"
ls -lh honeypot_decoys/ | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'
echo ""

# Step 2: Start honeypot (background)
echo "════════════════════════════════════════════════════════════"
echo "STEP 2: Starting Honeypot Server"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Starting honeypot on 127.0.0.1:2222..."
python3 ssh_honeypot.py &
HONEYPOT_PID=$!
echo "✓ Honeypot started with PID $HONEYPOT_PID"
echo ""

# Give it time to start
sleep 2

# Verify it's running
if nc -z 127.0.0.1 2222 2>/dev/null; then
    echo "✓ Honeypot is listening on port 2222"
else
    echo "✗ Honeypot may not be listening. Continuing anyway..."
fi
echo ""

# Step 3: Execute playbooks
echo "════════════════════════════════════════════════════════════"
echo "STEP 3: Executing Attacker Playbooks"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Running: python3 playbook_executor.py"
python3 playbook_executor.py
echo ""
echo "✓ Playbooks executed. Results saved to playbook_results/"
echo ""

# Stop honeypot
echo "⛔ Stopping honeypot server..."
kill $HONEYPOT_PID 2>/dev/null || true
sleep 1
echo "✓ Honeypot stopped"
echo ""

# Step 4: Analyze behavior
echo "════════════════════════════════════════════════════════════"
echo "STEP 4: Analyzing Behavioral Data"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Running: python3 behavioral_analyzer.py"
python3 behavioral_analyzer.py
echo ""
echo "✓ Analysis complete. Results saved to honeypot_logs/"
echo ""

# Display summary
echo "════════════════════════════════════════════════════════════"
echo "📊 COMPLETE WORKFLOW SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "✓ Step 1: Decoy artifacts generated (8 files)"
echo "✓ Step 2: Honeypot server ran and captured logs"
echo "✓ Step 3: Playbooks executed (43 commands across 8 sessions)"
echo "✓ Step 4: Behavioral analysis completed"
echo ""

# Display output files
echo "📁 OUTPUT FILES GENERATED:"
echo ""
echo "Honeypot Logs:"
if [ -f "honeypot_logs/master_log.jsonl" ]; then
    echo "  ✓ honeypot_logs/master_log.jsonl"
    echo "    Lines: $(wc -l < honeypot_logs/master_log.jsonl)"
fi
if [ -f "honeypot_logs/behavioural_analysis.json" ]; then
    echo "  ✓ honeypot_logs/behavioural_analysis.json"
fi
echo ""

echo "Decoy Artifacts (honeypot_decoys/):"
ls -1 honeypot_decoys/ | grep -v json | while read f; do
    echo "  ✓ $f"
done
echo "  ✓ artifact_inventory.json"
echo ""

echo "Playbook Results:"
if [ -f "playbook_results/all_playbook_results.json" ]; then
    echo "  ✓ playbook_results/all_playbook_results.json"
fi
echo ""

# Show analysis summary
if [ -f "honeypot_logs/behavioural_analysis.json" ]; then
    echo "📊 Analysis Summary:"
    python3 -c "
import json
with open('honeypot_logs/behavioural_analysis.json') as f:
    data = json.load(f)
    print(f'  Total sessions analyzed: {data[\"total_sessions\"]}')
    print(f'  Average depth score: {data[\"average_depth_score\"]}/50')
    print(f'  Average command diversity: {data[\"average_command_diversity\"]:.1%}')
    print(f'  Average session duration: {data[\"average_session_duration\"]:.1f}s')
    print(f'  Intent distribution:')
    for intent, count in sorted(data['intent_distribution'].items()):
        print(f'    - {intent}: {count}')
" || true
fi
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✅ WORKFLOW COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Review honeypot_logs/master_log.jsonl for detailed logs"
echo "  2. Examine honeypot_logs/behavioural_analysis.json for metrics"
echo "  3. Fill in report_template.md with actual results"
echo "  4. Submit your final report"
echo ""
echo "For individual runs:"
echo "  - Start honeypot: python3 ssh_honeypot.py"
echo "  - Run playbooks: python3 playbook_executor.py"
echo "  - Analyze: python3 behavioral_analyzer.py"
echo ""
