import { spawn } from 'node:child_process';

// spawn, not spawnSync: spawnSync blocks the calling test process's event
// loop, which would starve any in-process fixture server (e.g. cli.test.js's
// http.createServer) of a chance to handle the request while the child waits
// for a response - a deadlock (both ends stuck), not slowness. Both stdout
// and stderr are drained via 'data' listeners so a chatty child can never
// fill a pipe and block on an unread stream.
//
// Deliberately low-level: just runs `node <scriptPath> ...args` in `cwd` and
// resolves the raw process result. Callers that need JSON-line parsing or
// single-line assertions layer that on top (see cli.test.js's `run`).
export function runCli(scriptPath, args, cwd) {
  return new Promise((resolve, reject) => {
    const proc = spawn(process.execPath, [scriptPath, ...args], { cwd });
    proc.stdout.setEncoding('utf8');
    proc.stderr.setEncoding('utf8');
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (chunk) => { stdout += chunk; });
    proc.stderr.on('data', (chunk) => { stderr += chunk; });
    proc.on('error', reject);
    proc.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}
