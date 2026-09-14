// STEP JSON v0(docs/STEP_JSON-V0_PLAN_2026-09-15.md)。Failure Event の 1 行の版と、版つきの行を作る関数、スキーマの読み込み。
//
// 【値は変えない】D1 の lib が作る FailureEvent の先頭に schemaVersion を足すだけ(計画 J-2)。
// 【置き場所】計画 6.1 は lib/failureEvent.ts に置く予定だった。D3 が同じファイルを触っているので、衝突を避けて
// このファイルに分けた(計画書 §10.1 に書いた)。
// 【版を上げるとき】スキーマのファイルを版ごとに 1 つ増やし、古い版のファイルは消さない(計画 3.2)。

import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";
import type { FailureEvent } from "./failureEvent.js";

export const FAILURE_EVENT_SCHEMA_VERSION = "0.1" as const;

/** `--events` の 1 行(版つき)。版の欄は先頭に置く */
export type FailureEventLine = { schemaVersion: typeof FAILURE_EVENT_SCHEMA_VERSION } & FailureEvent;

export function toEventLine(event: FailureEvent): FailureEventLine {
  return { schemaVersion: FAILURE_EVENT_SCHEMA_VERSION, ...event };
}

/** この版のスキーマのファイル(scripts/playtest/schemas/failure-event.v<版>.schema.json) */
export const FAILURE_EVENT_SCHEMA_URL = new URL(`../schemas/failure-event.v${FAILURE_EVENT_SCHEMA_VERSION}.schema.json`, import.meta.url);

export function loadFailureEventSchema(): JsonSchema {
  return JSON.parse(readFileSync(FAILURE_EVENT_SCHEMA_URL, "utf-8")) as JsonSchema;
}

/** 1 行(JSON.parse した値)を、この版のスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った) */
export function validateFailureEventLine(line: unknown, schema: JsonSchema = loadFailureEventSchema()): string[] {
  return validate(line, schema);
}
