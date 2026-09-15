// STEP U6-I4 の 2 つ目の変更。check.ts の「## ②の名指し」の配線を見張る。
// docs/STEP_U6-I4_CHECK_TABLE_PLAN_2026-09-13.md 5.2(D-3 (イ))。
//
// 【2 つ置く理由】
// - ソース照合 … 呼び出しの 1 行を消す・渡す records の書き方を変える、を捕まえる。
//   **照合は片側にしか壊れない**(U6-R 計画書 7. の Y08〜Y10b。文字列を残して意味を変える書き換えは捕まらない)。
// - 子プロセス … check.ts を実際に走らせ、表の入力ごとの行と合計の行が、同じ records を
//   この試験のプロセスで数えた値と一致することを確かめる。**文字列を残して意味を変える書き換えも、
//   数字が変われば捕まる。** 期待値は data から切り離してある(件数を固定しない ― P-20)。
//
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる(skip は書かない)。
// 【一時ディレクトリ以外に書かない】走らせる前と後で、リポジトリの git status が同じであることを確かめる
// (共有ツリーで他のセッションが同時に保存すると落ちうる。安全側に壊れる。測るのは worktree で)。

import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { explainPositionWithStatus } from "../../apps/server/src/analysis/explanationGenerator.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../../apps/server/src/analysis/moveHistory.js";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../apps/server/src/api/stateResponse.js";
import type { RecordLine } from "./invariants/types.js";
import {
  countUndetermined,
  summarizeIntentStatements,
  UNDETERMINED_REASONS,
  type IntentStatementCounts,
  type UndeterminedReason,
} from "./lib/intentStatement.js";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const CHECK_TS = join(PLAYTEST_DIR, "check.ts");
const SECTION_HEADING = "## ②の名指し(STEP U6-I4)";

function basePlan(): ReachablePlanBody {
  return {
    reachableShapes: [],
    routes: [],
    targetShapeProgress: null,
    candidateMoveLabels: {},
    lastMoveOutcome: null,
    nextConsiderations: [],
    candidateMoveState: "unavailable",
    focusTextState: "pending",
    candidateMove: undefined,
    pendingReviewNote: null,
    resolvedTargetShapeId: null,
    shapeWeakness: null,
    urgentMessages: [],
    referenceShapes: [],
    directionNote: null,
    planChanged: false,
    planChangeReason: null,
  };
}

/** 固定棋譜 1 局から、T-1 と同じ作り方で ready 行を作る(②③ は本番の explainPositionWithStatus。エンジン不要)。 */
function recordsOfKifu(kifuFile: string): RecordLine[] {
  const moves: string[] = JSON.parse(readFileSync(join(PLAYTEST_DIR, "kifu", kifuFile), "utf8")).moves;
  const records: RecordLine[] = [];
  for (let ply = 0; ply <= moves.length; ply += 2) {
    const moveHistory = moves.slice(0, ply);
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const response: StateResponseBodyWithPlan = {
      sfen: finalSfen,
      moveHistory,
      status: { isEnd: false, outcome: undefined },
      coach: explainPositionWithStatus(finalSfen, moveHistory),
      legalMoves: [],
      escapeSquareThreats: [],
      moveHistoryJapanese: [],
      plan: basePlan(),
    };
    records.push({ kind: "record", ply, sfen: finalSfen, senteMove: null, goteMove: null, phase: "ready", elapsedMs: 0, response });
  }
  return records;
}

/** 「## ②の名指し」の節から、その対象の行(列の表の行と、理由別の表の行)を取り出す。 */
function rowsOf(stdout: string, label: string): string[] {
  const section = stdout.split(SECTION_HEADING)[1]?.split("\n## ")[0] ?? "";
  return section.split("\n").filter((line) => line.startsWith(`| ${label} | `));
}

/** 同じ件数を、表の 2 行の形にする(比べるのは数字。形が変われば安全側に落ちる)。 */
function expectedRows(label: string, c: IntentStatementCounts): string[] {
  const reasons = Object.keys(UNDETERMINED_REASONS) as UndeterminedReason[];
  return [
    `| ${label} | ${c.totalPlies} | ${c.noCandidate} | ${c.muted} | ${c.spokeLatest + c.spokeOlder} | ${c.spokeLatest} | ${c.spokeOlder} | ${countUndetermined(c)} |`,
    `| ${label} | ${reasons.map((reason) => c.undetermined[reason]).join(" | ")} |`,
  ];
}

// 【git status の引数(2026-09-14 の独立監査 B の必須 1 と、その再確認)】
// - --ignored: check.ts が実際にファイルを書く唯一の経路(--json)の置き場は gitignore 対象の
//   scripts/playtest/out/ である。無いと、無視される場所への書き込みが前後で同じに見える。
// - --untracked-files=all: normal だと無視されるディレクトリの中身が 1 行(!! scripts/playtest/out/)に
//   まとまり、out/ に既存のファイルが 1 つでもあると、書き足しても前後の出力が同じになる。
// - node_modules だけを pathspec で除く。**2 つ並べる必要がある**: 共有ツリーでは実ディレクトリの中身が
//   1 本ずつ出て **/node_modules/** でしか除けず、worktree ではシンボリックリンクが 1 本の ?? として出て
//   **/node_modules でしか除けない(計画書 9.4 の表)。
// 限界: node_modules の下への書き込みは、この試験では見えない。
const gitStatus = (): string =>
  execFileSync(
    "git",
    [
      "status",
      "--porcelain",
      "-z",
      "--untracked-files=all",
      "--ignored",
      "--",
      ".",
      ":(exclude,glob)**/node_modules",
      ":(exclude,glob)**/node_modules/**",
    ],
    { cwd: REPO_ROOT },
  ).toString();

describe("check.ts の「## ②の名指し」(計画書 5.2)", () => {
  it("ソース照合: 他の表と同じ records を渡して組み立て、描いた行を積み、renderMarkdown に渡している", () => {
    const source = readFileSync(CHECK_TS, "utf8");
    expect(source).toContain(
      "  const intentStatementReport = buildIntentStatementReport(inputs.map((i) => ({ kifuId: i.kifuId, records: i.records, initialSfen: i.initialSfen })));",
    );
    expect(source).toContain("  lines.push(...renderIntentStatementTables(intentStatementReport));");
    expect(source).toContain(
      "  console.log(renderMarkdown(inputs, allFindings, groups, denominatorReport, searchPvReport, intentStatementReport));",
    );
  });

  it(
    "子プロセス: 2 入力の JSONL に check.ts を掛けると exit 0 で、入力ごとと合計の行が、同じ records を数えた値と一致する",
    () => {
      const inputs = [
        { kifuId: "u6i4-a", records: recordsOfKifu("2026-09-10-claude-10moves.json") },
        { kifuId: "u6i4-b", records: recordsOfKifu("2026-09-12-live-30moves-claude-2-round2.json") },
      ];
      const dir = mkdtempSync(join(tmpdir(), "u6i4-check-"));
      try {
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          const meta = { kind: "meta", kifuId: input.kifuId, startedAt: "t", gitHead: null, enginePath: "-" };
          writeFileSync(filePath, `${[meta, ...input.records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });

        const before = gitStatus();
        // exit code が 0 以外なら execFileSync が例外を投げる(=赤)。npx・tsx が無くても例外で赤。
        const stdout = execFileSync("npx", ["tsx", CHECK_TS, ...paths], { cwd: REPO_ROOT, encoding: "utf-8" });
        const after = gitStatus();

        expect(after).toBe(before);
        expect(readdirSync(dir).sort()).toEqual(paths.map((p) => p.slice(dir.length + 1)).sort());
        for (const input of inputs) {
          expect(rowsOf(stdout, input.kifuId), input.kifuId).toEqual(expectedRows(input.kifuId, summarizeIntentStatements([{ records: input.records, initialSfen: DEFAULT_INITIAL_SFEN }])));
        }
        const total = summarizeIntentStatements(inputs.map((input) => ({ records: input.records, initialSfen: DEFAULT_INITIAL_SFEN })));
        expect(rowsOf(stdout, "合計"), "合計").toEqual(expectedRows("合計", total));
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});

// ---- STEP D0-SIDE 段 2(R-6・R-7): check.ts は meta から読んだ開始局面を、②の表と不変条件の両方へ渡す ----
// 開始局面 FOLD_START は、平手・後手番の初期局面に 3c3d を当てた局面(計画 F-S8。手で導いた値)。
const FOLD_START = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";

describe("check.ts と開始局面(STEP D0-SIDE 段 2)", () => {
  it(
    "子プロセス: 同じ記録を meta が mirrored: true の入力と平手の入力で渡すと、②の表の U-2 は前者だけ 0、I-9 の所見は前者だけに出る",
    () => {
      const moveHistory = ["6i5h"];
      const { finalSfen } = replayMoveHistory(moveHistory, FOLD_START);
      const response: StateResponseBodyWithPlan = {
        sfen: finalSfen,
        moveHistory,
        status: { isEnd: false, outcome: undefined },
        coach: explainPositionWithStatus(finalSfen, moveHistory, { initialSfen: FOLD_START }),
        legalMoves: [],
        escapeSquareThreats: [],
        moveHistoryJapanese: [],
        plan: {
          ...basePlan(),
          targetShapeProgress: {
            shapeId: "mino_honmino",
            name: "本美濃囲い",
            description: "",
            matchedSquareLabels: [],
            matchedSquares: [],
            matchedPieceLabels: [],
            missingSquareLabels: [],
            missingSquares: ["2h", "3h"],
            pendingReviewNote: null,
          },
        },
      };
      const record: RecordLine = { kind: "record", ply: 2, sfen: finalSfen, senteMove: null, goteMove: null, phase: "ready", elapsedMs: 0, response };
      const base = { kind: "meta", startedAt: "t", gitHead: null, enginePath: "-" };
      const inputs = [
        { kifuId: "d0side-folded", meta: { ...base, kifuId: "d0side-folded", mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FOLD_START }, initialSfen: FOLD_START },
        { kifuId: "d0side-plain", meta: { ...base, kifuId: "d0side-plain" }, initialSfen: DEFAULT_INITIAL_SFEN },
      ];
      // 前提(このプロセスの lib で数えた値): 開始局面を渡せば U-2 は 0、平手なら 1
      const foldedCounts = summarizeIntentStatements([{ records: [record], initialSfen: FOLD_START }]);
      const plainCounts = summarizeIntentStatements([{ records: [record], initialSfen: DEFAULT_INITIAL_SFEN }]);
      expect(foldedCounts.undetermined["U-2"]).toBe(0);
      expect(plainCounts.undetermined["U-2"]).toBe(1);

      const dir = mkdtempSync(join(tmpdir(), "d0side-check-"));
      try {
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          writeFileSync(filePath, `${[input.meta, record].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const before = gitStatus();
        const stdout = execFileSync("npx", ["tsx", CHECK_TS, ...paths], { cwd: REPO_ROOT, encoding: "utf-8" });
        expect(gitStatus()).toBe(before);

        expect(rowsOf(stdout, "d0side-folded")).toEqual(expectedRows("d0side-folded", foldedCounts));
        expect(rowsOf(stdout, "d0side-plain")).toEqual(expectedRows("d0side-plain", plainCounts));
        const total = summarizeIntentStatements(inputs.map((input) => ({ records: [record], initialSfen: input.initialSfen })));
        expect(rowsOf(stdout, "合計")).toEqual(expectedRows("合計", total));

        const i9Section = stdout.split("### I-9(")[1]?.split("\n### ")[0]?.split("\n---")[0] ?? "";
        expect(i9Section, "I-9 の節が無い").not.toBe("");
        expect(i9Section).toContain("- 発生箇所(kifuId#ply): d0side-folded#2");
        expect(i9Section).not.toContain("d0side-plain#2");
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});
