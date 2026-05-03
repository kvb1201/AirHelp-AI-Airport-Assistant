#!/usr/bin/env node
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';

function resolvePython() {
  for (const cmd of ['python3', 'python']) {
    const r = spawnSync(cmd, ['-c', 'import sys; sys.exit(0)'], {
      stdio: 'pipe',
      shell: false,
    });
    if (r.status === 0) return cmd;
  }
  console.error('Need python3 or python on PATH.');
  process.exit(1);
}

function venvPaths() {
  const dir = path.join(REPO, '.venv');
  if (isWin) {
    return {
      dir,
      python: path.join(dir, 'Scripts', 'python.exe'),
      pip: path.join(dir, 'Scripts', 'pip.exe'),
    };
  }
  return {
    dir,
    python: path.join(dir, 'bin', 'python'),
    pip: path.join(dir, 'bin', 'pip'),
  };
}

function run(cmd, args, opts = {}) {
  const cwd = opts.cwd ?? REPO;
  const shell = opts.shell !== undefined ? opts.shell : isWin;
  const r = spawnSync(cmd, args, {
    cwd,
    stdio: 'inherit',
    env: process.env,
    shell,
  });
  if (r.error) throw r.error;
  if (r.status !== 0 && r.status !== null) process.exit(r.status);
}

function ensureVenv() {
  const { python, pip } = venvPaths();
  if (!fs.existsSync(python)) {
    const py = resolvePython();
    run(py, ['-m', 'venv', '.venv'], { cwd: REPO, shell: false });
  }
  if (!fs.existsSync(python)) {
    console.error('Python venv failed. Install Python 3 and ensure `python` is on PATH.');
    process.exit(1);
  }
  return { python, pip };
}

const requirements = path.join(REPO, 'backend', 'requirements.txt');
const frontend = path.join(REPO, 'frontend');
const backend = path.join(REPO, 'backend');

function help() {
  console.log(`From repo root:

  npm run setup         first time (Python deps + frontend npm; includes piper-tts)
  npm run piper:setup   .venv + piper-tts + English ONNX voice (good for TTS-only / new machine)
  npm run piper:install install/upgrade piper-tts in .venv only
  npm run piper:voices  download English voice into backend/app/data/piper_voices (curl)
  npm run dev           frontend  http://localhost:3000
  npm run api           backend   http://localhost:8000
  npm run scrape        scrape CSMIA T2 outlets + live flight status (Playwright)
  npm run test          quick check

  Optional env (see .env.example): PIPER_VOICE_EN, PIPER_BINARY, PIPER_TEST_VOICE_ONNX
`);
}

/** Bash is required for scripts/download_piper_voices.sh (Git Bash on Windows). */
function runBashScript(relFromRepo) {
  const script = path.join(REPO, relFromRepo);
  if (!fs.existsSync(script)) {
    console.error(`Missing script: ${script}`);
    process.exit(1);
  }
  const r = spawnSync('bash', [script], { cwd: REPO, stdio: 'inherit', env: process.env, shell: false });
  if (r.error) {
    console.error(r.error.message);
    console.error('Install Git Bash (Windows) or use WSL/macOS/Linux so `bash` is on PATH.');
    process.exit(1);
  }
  if (r.status !== 0 && r.status !== null) process.exit(r.status);
}

function piperVoices() {
  runBashScript(path.join('scripts', 'download_piper_voices.sh'));
}

function piperInstall() {
  const { pip } = ensureVenv();
  run(pip, ['install', '--upgrade', 'pip'], { shell: false });
  run(pip, ['install', 'piper-tts>=1.4.0,<2'], { shell: false });
}

function piperSetup() {
  piperInstall();
  piperVoices();
  console.log(`
Piper setup done.
  • Voice files: backend/app/data/piper_voices/ (gitignored *.onnx — each machine downloads its own)
  • Optional .env: PIPER_VOICE_EN, PIPER_BINARY, PIPER_TEST_VOICE_ONNX — see .env.example
`);
}

function install() {
  const { python, pip } = ensureVenv();
  run(python, ['-m', 'pip', 'install', '--upgrade', 'pip'], { shell: false });
  run(pip, ['install', '-r', requirements], { shell: false });
}

function installFrontend() {
  run('npm', ['install'], { cwd: frontend });
}

function setup() {
  install();
  run('npm', ['install'], { cwd: REPO, shell: isWin });
  installFrontend();
  console.log('setup done.');
}

function dev() {
  run('npm', ['run', 'dev'], { cwd: frontend });
}

function api() {
  const { python } = venvPaths();
  if (!fs.existsSync(python)) {
    console.error('Run npm run setup first.');
    process.exit(1);
  }
  run(python, ['run.py'], { cwd: backend, shell: false });
}

function scrape() {
  const { python } = venvPaths();
  if (!fs.existsSync(python)) {
    console.error('Run npm run setup first.');
    process.exit(1);
  }
  run(python, ['scrape_csmia_t2.py'], { cwd: backend, shell: false });
  run(process.execPath, [path.join(REPO, 'scripts', 'scrape_csmia_flights.mjs')], { cwd: REPO, shell: false });
  run(
    python,
    ['-c', 'from app.services.rag_service import build_knowledge_base; build_knowledge_base()'],
    { cwd: backend, shell: false },
  );
}

function test() {
  const { python } = venvPaths();
  if (!fs.existsSync(python)) {
    console.error('Run npm run setup first.');
    process.exit(1);
  }
  const nm = path.join(frontend, 'node_modules');
  if (!fs.existsSync(nm)) {
    console.error('Run npm run setup first.');
    process.exit(1);
  }
  run(python, ['-c', 'from app.main import app; print("backend import ok:", app.title)'], {
    cwd: backend,
    shell: false,
  });
  run('npm', ['run', 'build'], { cwd: frontend });
  console.log('test ok');
}

const task = process.argv[2] || 'help';
const tasks = {
  help,
  setup,
  dev,
  api,
  scrape,
  test,
  'piper-voices': piperVoices,
  'piper-install': piperInstall,
  'piper-setup': piperSetup,
};

const fn = tasks[task];
if (!fn) {
  console.error(`Unknown: ${task}\n`);
  help();
  process.exit(1);
}
fn();
