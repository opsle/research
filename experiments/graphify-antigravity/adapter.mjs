import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';

const [promptPath, schemaPath, outputPath] = process.argv.slice(2);
if (!promptPath || !schemaPath || !outputPath) throw new Error('usage: adapter PROMPT SCHEMA OUTPUT');
const prompt = readFileSync(promptPath, 'utf8');
const run = spawnSync('agy', ['--print', prompt, '--mode', 'plan', '--sandbox', '--disable-slash-commands', '--json-schema', schemaPath, '--output-format', 'json', '--print-timeout', '10m'], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, timeout: 11 * 60 * 1000 });
if (run.status !== 0) throw new Error('Antigravity failed; inspect a private bounded log');
const envelope = JSON.parse(run.stdout);
const fragment = envelope.structured_output ?? envelope.response;
if (!fragment || typeof fragment !== 'object') throw new Error('structured output missing');
writeFileSync(outputPath, JSON.stringify({ fragment, usage: envelope.usage ?? null }, null, 2));
