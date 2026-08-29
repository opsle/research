#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value === null || typeof value !== 'object') return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
}

const [profilerRoot, inputPath] = process.argv.slice(2);
if (!profilerRoot || !inputPath) {
  process.stderr.write('usage: interop-profile.mjs PROFILER_ROOT INPUT\n');
  process.exit(2);
}

const api = await import(pathToFileURL(resolve(profilerRoot, 'src/context-evidence.js')).href);
const input = JSON.parse(await readFile(inputPath, 'utf8'));
const events = [];

if (input.kind === 'raw') {
  events.push(api.rawBaselineEvent({
    armId: input.arm_id,
    configurationId: input.configuration_id,
    contentIdentity: input.raw_identity,
    eventId: `${input.run_id}:raw`,
    evidenceCount: input.evidence_count,
    operationId: input.operation_id,
    rawBytes: input.raw_bytes,
  }));
} else {
  events.push(api.contextFirewallEventFromPacket({
    armId: input.arm_id,
    configurationId: input.configuration_id,
    eventId: `${input.run_id}:packet`,
    packet: input.packet,
    packetBytes: Buffer.from(input.packet_bytes_base64, 'base64'),
    validation: input.validation,
  }));
  if (input.escalation !== 'NONE') {
    events.push(api.escalationEvent({
      escalationId: `${input.run_id}:escalation`,
      eventId: `${input.run_id}:escalation-requested`,
      operationId: input.operation_id,
      reason: input.escalation_reason,
      reasonCategory: 'PACKET_REQUIRES_RAW',
      status: 'REQUESTED',
    }));
  }
  if (input.escalation === 'FULFILLED') {
    events.push(api.escalationEvent({
      escalationId: `${input.run_id}:escalation`,
      eventId: `${input.run_id}:escalation-fulfilled`,
      exposure: {
        bytes: input.raw_bytes,
        content_identity: input.raw_identity,
      },
      operationId: input.operation_id,
      reason: 'Exact content-addressed raw oracle transcript exposed once.',
      reasonCategory: 'PACKET_REQUIRES_RAW',
      sourceRelation: 'SUBSET_OF_RAW',
      status: 'FULFILLED',
    }));
  }
}

const trajectory = {
  events,
  protocol_version: api.TRAJECTORY_PROTOCOL,
  run: {
    arm_id: input.arm_id,
    configuration_id: input.configuration_id,
    run_id: input.run_id,
    task_id: input.task_id,
  },
};
const profile = api.profileTrajectory(trajectory);
process.stdout.write(`${JSON.stringify(canonicalize(profile))}\n`);
process.stderr.write(`[Trajectory Profiler] ${input.run_id} | ${profile.measurement_status} | ${profile.valid ? 'valid' : 'rejected'}\n`);
process.exitCode = profile.valid ? 0 : 1;
