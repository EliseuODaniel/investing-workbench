import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, '..');
const task = process.argv[2] ?? 'all';
const extraArgs = process.argv.slice(3);
const supportedNodeMajor = 22;

const nodeExecutable = process.execPath;
const eslintEntrypoint = path.join(frontendRoot, 'node_modules', 'eslint', 'bin', 'eslint.js');
const tscEntrypoint = path.join(frontendRoot, 'node_modules', 'typescript', 'bin', 'tsc');
const viteEntrypoint = path.join(frontendRoot, 'node_modules', 'vite', 'bin', 'vite.js');
const vitestRunnerEntrypoint = path.join(frontendRoot, 'scripts', 'run-vitest-sequential.mjs');

ensureSupportedNodeRuntime();

switch (task) {
  case 'lint':
    await runNodeScript(eslintEntrypoint, [
      '.',
      '--ext',
      'ts,tsx',
      '--report-unused-disable-directives',
      '--max-warnings',
      '0',
      ...extraArgs,
    ]);
    break;
  case 'test':
    await runNodeScript(vitestRunnerEntrypoint, extraArgs.length > 0 ? extraArgs : ['--run']);
    break;
  case 'build':
    await runNodeScript(tscEntrypoint, extraArgs);
    await runNodeScript(viteEntrypoint, ['build']);
    break;
  case 'all':
    await runNodeScript(eslintEntrypoint, [
      '.',
      '--ext',
      'ts,tsx',
      '--report-unused-disable-directives',
      '--max-warnings',
      '0',
    ]);
    await runNodeScript(vitestRunnerEntrypoint, ['--run']);
    await runNodeScript(tscEntrypoint, []);
    await runNodeScript(viteEntrypoint, ['build']);
    break;
  default:
    throw new Error(`Unknown frontend task "${task}". Expected lint, test, build, or all.`);
}

function runNodeScript(scriptPath, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(nodeExecutable, [scriptPath, ...args], {
      cwd: frontendRoot,
      stdio: 'inherit',
      env: process.env,
    });

    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(
        new Error(
          `Frontend task failed for ${path.basename(scriptPath)} with exit code ${code ?? 'unknown'}`
        )
      );
    });
  });
}

function ensureSupportedNodeRuntime() {
  const major = Number.parseInt(process.versions.node.split('.')[0] ?? '', 10);
  if (major === supportedNodeMajor) {
    return;
  }

  throw new Error(
    `Frontend tooling expects Node ${supportedNodeMajor}.x. Current runtime: ${process.version}. `
      + 'Use frontend/.nvmrc or frontend/.node-version before running npm scripts.'
  );
}
