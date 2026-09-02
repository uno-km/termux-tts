#!/usr/bin/env node
/**
 * termux-tts Node.js Global CLI Wrapper
 * Cross-platform entry point for npm global execution.
 */
const { spawn } = require('child_process');
const path = require('path');

const args = process.argv.slice(2);
const pyBin = process.env.PYTHON_BIN || (process.platform === 'win32' ? 'py' : 'python3');

// 1. Try running module entry point directly
const pyProcess = spawn(pyBin, ['-m', 'termux_tts.cli', ...args], {
    stdio: 'inherit',
    env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
});

pyProcess.on('error', (err) => {
    // 2. Fallback to standalone binary
    const binProcess = spawn('termux-tts', args, { stdio: 'inherit' });
    binProcess.on('error', (bErr) => {
        console.error('[ERROR] Failed to execute termux-tts CLI:', bErr.message);
        process.exit(1);
    });
    binProcess.on('close', (code) => {
        process.exit(code || 0);
    });
});

pyProcess.on('close', (code) => {
    process.exit(code || 0);
});

