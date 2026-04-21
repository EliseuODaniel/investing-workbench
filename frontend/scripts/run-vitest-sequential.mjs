import { readdir } from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, '..');
const vitestEntrypoint = path.join(frontendRoot, 'node_modules', 'vitest', 'vitest.mjs');
const rootArgv = process.argv.slice(2);

const positionalArgs = rootArgv.filter((arg) => !arg.startsWith('-'));
const extraArgs = rootArgv.filter((arg) => arg.startsWith('-') && arg !== '--run');

const explicitFiles = positionalArgs.filter((arg) => arg.includes('.test.'));
const files = explicitFiles.length > 0 ? explicitFiles : await collectTestFiles();

for (const file of files) {
  await runVitestForFile(file, extraArgs);
}

async function collectTestFiles() {
  const discovered = [];
  await walk(path.join(frontendRoot, 'src'), discovered);
  return discovered.sort().map((filePath) => path.relative(frontendRoot, filePath));
}

async function walk(dir, discovered) {
  const entries = await readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(fullPath, discovered);
      continue;
    }
    if (entry.name.endsWith('.test.ts') || entry.name.endsWith('.test.tsx')) {
      discovered.push(fullPath);
    }
  }
}

function runVitestForFile(file, extraCliArgs) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      process.execPath,
      [vitestEntrypoint, '--run', file, '--maxWorkers=1', ...extraCliArgs],
      {
        cwd: frontendRoot,
        stdio: 'inherit',
        env: process.env,
      }
    );

    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`Vitest failed for ${file} with exit code ${code ?? 'unknown'}`));
    });
  });
}
