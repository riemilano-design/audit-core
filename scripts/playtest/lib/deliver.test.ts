// STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 3)。lib/deliver.ts(純粋な部分)の試験。
// 流儀は lib/pipeline.test.ts と同じ(偽の fs / probe を注入し、引数の並びと済みの判定だけを見る)。
// **将棋の判断・数の集計はここにも無い**(引数の組み立てと段の順だけ)。

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";

import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  answerFactsCommand,
  answerMaterialFlags,
  checkAnswerCommand,
  checkDeliveryCommand,
  checkStructureCommand,
  DELIVER_SEND_DIRS,
  DELIVER_STAGES,
  DeliverArgError,
  deliverLogArgsLineOf,
  deliverLogLineOf,
  deliverOutPaths,
  deliverSendNames,
  deliverSendPaths,
  DELIVER_ORIGINAL_KEYS,
  exitSendPairs,
  exitSendPatientPath,
  sendCopyDecisions,
  directAnswersCommand,
  exitBodyCommand,
  exitCandidatesCommand,
  exitCoverCommand,
  exitDraftCommand,
  exitGateCommand,
  exitFillCommand,
  exitPacketPaths,
  customerDirOf,
  exitSelectPaths,
  exitRenderCommand,
  exitSourceIndexPairs,
  finalPositionsCommand,
  finalPositionsPartPath,
  groupLabelOf,
  groupListOf,
  groupPaths,
  groupsWithRead,
  KIFU_NAME_FIXED_ALLOWED_NUMBERS,
  kifuNameProblems,
  materialPlanOf,
  materialsPending,
  mergeFinalPositions,
  pageIndexNameOf,
  parseDeliverArgs,
  PERSON_REFERENT,
  pipelineCommand,
  pipelineGateCommand,
  planDeliver,
  renderAnswerCommand,
  renderTimeCauseCommand,
  reportDataDirEnv,
  seatSecondsOf,
  stagesFrom,
  timeCauseCommand,
  timeSearchCommand,
  TODO_MARK,
  unexpectedOutFiles,
  type DeliverArgs,
  type DeliverProbe,
} from "./deliver.js";
import { groupLabelOfTimeLimitSec } from "./directAnswers.js";
import { PipelineConfigError } from "./pipeline.js";

// ---- 偽の probe(見えているものを表で与える) ----

interface FakeWorld {
  files?: string[];
  jsonlDirs?: string[];
  fixed?: Record<string, string[]>;
  losses?: Record<string, number>;
  mtimes?: Record<string, number>;
}

function fakeProbe(world: FakeWorld): DeliverProbe {
  return {
    exists: (p) => (world.files ?? []).includes(p),
    hasJsonl: (d) => (world.jsonlDirs ?? []).includes(d),
    fixedKifuFiles: (d) => world.fixed?.[d] ?? [],
    timeUpLossCount: (p) => world.losses?.[p] ?? 0,
    mtimeMs: (p) => world.mtimes?.[p],
  };
}

const BASE_ARGV = [
  "--person",
  "p2",
  "--kifu-dir",
  "/w/kifu",
  "--work",
  "/w/now",
  "--time-limit-sec",
  "180",
  "--name",
  "お客さま",
  "--title",
  "題",
  "--today",
  "2026-09-24",
  "--out",
  "/w/out",
];

function argsOf(extra: readonly string[] = []): DeliverArgs {
  return parseDeliverArgs([...BASE_ARGV, ...extra]);
}

// ---- 引数の解釈 ----

describe("parseDeliverArgs", () => {
  it("必須の引数だけで読める(パスは絶対パスになる)", () => {
    const args = argsOf();
    expect(args.person).toBe("p2");
    expect(args.work).toBe("/w/now");
    expect(args.timeLimitSec).toBe(180);
    expect(args.dryRun).toBe(false);
    expect(args.forbid).toEqual([]);
  });

  it("渡さなかった任意の旗はキー自体が付かない(lib/pipeline.ts と同じ流儀)", () => {
    const args = argsOf();
    expect("previousWork" in args).toBe(false);
    expect("parallel" in args).toBe(false);
    expect("from" in args).toBe(false);
  });

  it("必須の旗が無ければ止まる", () => {
    expect(() => parseDeliverArgs(["--person", "p2"])).toThrow(DeliverArgError);
  });

  it("知らない旗・値の無い旗で止まる", () => {
    expect(() => argsOf(["--nope"])).toThrow(DeliverArgError);
    expect(() => parseDeliverArgs([...BASE_ARGV, "--parallel"])).toThrow(DeliverArgError);
  });

  it("--time-limit-sec・--parallel は正の整数だけ", () => {
    expect(() => parseDeliverArgs([...BASE_ARGV.slice(0, 7), "0", ...BASE_ARGV.slice(8)])).toThrow(DeliverArgError);
    expect(() => argsOf(["--parallel", "-1"])).toThrow(DeliverArgError);
  });

  it("--from は段の名前だけ", () => {
    expect(argsOf(["--from", "answer-check"]).from).toBe("answer-check");
    expect(() => argsOf(["--from", "nope"])).toThrow(DeliverArgError);
  });

  it("--forbid は繰り返せる", () => {
    expect(argsOf(["--forbid", "甲", "--forbid", "乙"]).forbid).toEqual(["甲", "乙"]);
  });

  // 1 コマンド化(指示書 §3.1・§3.5 の 1)。`lib/pipeline.ts` と同じ流儀であることを見る。
  describe("--compare-dir / --compare-person(段 pipeline-gate への中継)", () => {
    it("渡さなければ compareDirs は空・comparePerson はキー自体が付かない", () => {
      const args = argsOf();
      expect(args.compareDirs).toEqual([]);
      expect("comparePerson" in args).toBe(false);
    });

    it("--compare-dir は値を連続していくつでも取る(次の -- まで)", () => {
      const args = argsOf(["--compare-dir", "/c/a", "/c/b", "/c/c", "--compare-person", "p5"]);
      expect(args.compareDirs).toEqual(["/c/a", "/c/b", "/c/c"]);
      expect(args.comparePerson).toBe("p5");
    });

    it("値が無ければ止まる", () => {
      expect(() => argsOf(["--compare-dir", "--compare-person", "p5"])).toThrow(DeliverArgError);
    });

    it("片方だけでは止まる(必ず一緒に渡す)", () => {
      expect(() => argsOf(["--compare-dir", "/c/a"])).toThrow(DeliverArgError);
      expect(() => argsOf(["--compare-person", "p5"])).toThrow(DeliverArgError);
    });
  });

  describe("組の一覧(--group-work / --group-time-limit-sec)", () => {
    it("渡さなければ [前回, 今回] の順(前回が無ければ今回だけ)", () => {
      expect(argsOf().groups).toEqual([{ work: "/w/now", timeLimitSec: 180 }]);
      expect(argsOf(["--previous-work", "/w/prev"]).groups).toEqual([
        { work: "/w/prev", timeLimitSec: 180 },
        { work: "/w/now", timeLimitSec: 180 },
      ]);
    });

    it("渡した順がそのまま組の順になる(3 組)", () => {
      const args = argsOf([
        "--previous-work",
        "/w/prev",
        "--group-work",
        "/w/prev",
        "--group-time-limit-sec",
        "180",
        "--group-work",
        "/w/now",
        "--group-time-limit-sec",
        "180",
        "--group-work",
        "/w/long",
        "--group-time-limit-sec",
        "600",
      ]);
      expect(args.groups).toEqual([
        { work: "/w/prev", timeLimitSec: 180 },
        { work: "/w/now", timeLimitSec: 180 },
        { work: "/w/long", timeLimitSec: 600 },
      ]);
    });

    it("対の数が合わなければ止まる", () => {
      expect(() => argsOf(["--group-work", "/w/now"])).toThrow(DeliverArgError);
    });

    it("--work が一覧に無い / 2 回ある なら止まる", () => {
      expect(() => argsOf(["--group-work", "/w/other", "--group-time-limit-sec", "180"])).toThrow(DeliverArgError);
      expect(() => argsOf(["--group-work", "/w/now", "--group-time-limit-sec", "180", "--group-work", "/w/now", "--group-time-limit-sec", "180"])).toThrow(
        DeliverArgError,
      );
    });

    it("--previous-work が一覧に無ければ止まる", () => {
      expect(() => argsOf(["--previous-work", "/w/prev", "--group-work", "/w/now", "--group-time-limit-sec", "180"])).toThrow(DeliverArgError);
    });
  });
});

// ---- 顧客フォルダの名前と安全装置 ----

describe("deliverOutPaths・unexpectedOutFiles", () => {
  it("固定の名前を返す", () => {
    const out = deliverOutPaths("/w/out");
    expect(out.front).toBe("/w/out/1_まとめ.pdf");
    expect(out.answerDraft).toBe("/w/out/8_B_どうしたら_下書き.md");
    expect(out.directAnswers).toBe("/w/out/direct/direct_answers.json");
    expect(finalPositionsPartPath("/w/out", 0)).toBe("/w/out/direct/final_positions_1.json");
  });

  it("自分が書く名前だけなら空(final_positions_<i>.json も許す)", () => {
    expect(unexpectedOutFiles(["1_まとめ.pdf", "deliver_log.jsonl", "direct"], ["direct_answers.json", "final_positions_2.json"])).toEqual([]);
  });

  it("知らない名前があれば挙げる(取り違え防止)", () => {
    expect(unexpectedOutFiles(["0_添える文と感想票.md"], ["memo.json"])).toEqual(["0_添える文と感想票.md", "direct/memo.json"]);
  });
});

// ---- 段ごとの引数 ----

describe("pipelineCommand", () => {
  it("--until と --time-limit-sec を渡し、--previous は前回の patient を指す", () => {
    const args = argsOf(["--previous-work", "/w/prev", "--parallel", "3"]);
    expect(pipelineCommand(args, "report-data")).toEqual([
      "--person",
      "p2",
      "--kifu-dir",
      "/w/kifu",
      "--work",
      "/w/now",
      "--parallel",
      "3",
      "--whatif",
      "--until",
      "report-data",
      // **`--name` は `PERSON_REFERENT` 固定**(P-174 (ウ)。2026-09-29 の司令塔の決定)。
      // `args.name`(この試験では「お客さま」)は**渡さない** ― 付録 1 が顧客を名前で呼ぶ道を閉じる。
      "--name",
      PERSON_REFERENT,
      "--title",
      "題",
      "--today",
      "2026-09-24",
      "--time-limit-sec",
      "180",
      "--previous",
      "/w/prev/report/patient_report_data.json",
    ]);
  });

  it("--parallel・--previous-work が無ければその旗を足さない", () => {
    const flags = pipelineCommand(argsOf(), "pdf");
    expect(flags).not.toContain("--parallel");
    expect(flags).not.toContain("--previous");
    expect(flags.slice(-2)).toEqual(["--time-limit-sec", "180"]);
  });
});

describe("pipelineGateCommand", () => {
  it("--until gate と compare だけを足す(--whatif・--name・--title・--today・--time-limit-sec・--previous は付けない)", () => {
    const args = argsOf(["--previous-work", "/w/prev", "--parallel", "3", "--compare-dir", "/c/a", "/c/b", "--compare-person", "p5"]);
    expect(pipelineGateCommand(args)).toEqual([
      "--person",
      "p2",
      "--kifu-dir",
      "/w/kifu",
      "--work",
      "/w/now",
      "--parallel",
      "3",
      "--until",
      "gate",
      "--compare-dir",
      "/c/a",
      "/c/b",
      "--compare-person",
      "p5",
    ]);
  });

  it("--parallel が無ければその旗を足さない", () => {
    const flags = pipelineGateCommand(argsOf(["--compare-dir", "/c/a", "--compare-person", "p5"]));
    expect(flags).not.toContain("--parallel");
    expect(flags).toEqual(["--person", "p2", "--kifu-dir", "/w/kifu", "--work", "/w/now", "--until", "gate", "--compare-dir", "/c/a", "--compare-person", "p5"]);
  });

  it("compare が無ければ組めない(推測で補わない)", () => {
    expect(() => pipelineGateCommand(argsOf())).toThrow(DeliverArgError);
  });
});

describe("directAnswersCommand", () => {
  it("read/ がある組だけを組の順に、対 → 秒 の並びで渡す(make_direct.sh と同じ)", () => {
    const groups = [
      groupPaths({ work: "/w/a", timeLimitSec: 180 }, "p2"),
      groupPaths({ work: "/w/b", timeLimitSec: 600 }, "p2"),
    ];
    expect(directAnswersCommand(groups, "/w/out/direct/direct_answers.json")).toEqual([
      "--whatif-v2-dir",
      "/w/a/p2/whatif-v2",
      "--read-dir",
      "/w/a/p2/read",
      "--whatif-v2-dir",
      "/w/b/p2/whatif-v2",
      "--read-dir",
      "/w/b/p2/read",
      "--time-limit-sec",
      "180",
      "--time-limit-sec",
      "600",
      "--out",
      "/w/out/direct/direct_answers.json",
    ]);
  });

  it("組の順が結果の並びを決める(逆にすれば逆になる)", () => {
    const a = groupPaths({ work: "/w/a", timeLimitSec: 180 }, "p2");
    const b = groupPaths({ work: "/w/b", timeLimitSec: 600 }, "p2");
    const forward = directAnswersCommand([a, b], "/o");
    const backward = directAnswersCommand([b, a], "/o");
    expect(forward).not.toEqual(backward);
    expect(forward.indexOf("/w/a/p2/read")).toBeLessThan(forward.indexOf("/w/b/p2/read"));
    expect(backward.indexOf("/w/b/p2/read")).toBeLessThan(backward.indexOf("/w/a/p2/read"));
    // 秒の並びも組の順どおり(180 → 600 / 600 → 180)
    expect(forward.filter((_, i) => forward[i - 1] === "--time-limit-sec")).toEqual(["180", "600"]);
    expect(backward.filter((_, i) => backward[i - 1] === "--time-limit-sec")).toEqual(["600", "180"]);
  });
});

describe("groupsWithRead", () => {
  it("read/ に *.jsonl がある組だけを、組の順のまま返す", () => {
    const groups = [
      groupPaths({ work: "/w/a", timeLimitSec: 180 }, "p2"),
      groupPaths({ work: "/w/b", timeLimitSec: 180 }, "p2"),
      groupPaths({ work: "/w/c", timeLimitSec: 600 }, "p2"),
    ];
    const probe = fakeProbe({ jsonlDirs: ["/w/b/p2/read", "/w/c/p2/read"] });
    expect(groupsWithRead(groups, probe).map((g) => g.work)).toEqual(["/w/b", "/w/c"]);
  });
});

describe("finalPositionsCommand・mergeFinalPositions", () => {
  it("1 組ぶんの引数(make_direct.sh と同じ形)", () => {
    const g = groupPaths({ work: "/w/a", timeLimitSec: 180 }, "p2");
    expect(finalPositionsCommand(g, ["/k/1.fixed.json", "/k/2.fixed.json"], "/o/part.json")).toEqual([
      "--kifu",
      "/k/1.fixed.json",
      "/k/2.fixed.json",
      "--patient",
      "/w/a/report/patient_report_data.json",
      "--time-limit-sec",
      "180",
      "--out",
      "/o/part.json",
    ]);
  });

  it("先頭のファイルのメタ + entries を順に連結する", () => {
    const a = { kind: "final_positions", startedAt: "A", nodes: 1, entries: [{ id: 1 }, { id: 2 }] };
    const b = { kind: "final_positions", startedAt: "B", nodes: 1, entries: [{ id: 3 }] };
    const merged = mergeFinalPositions([a, b]);
    expect(merged["startedAt"]).toBe("A");
    expect(merged["entries"]).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }]);
  });

  it("連結の順が入れ替われば entries の順も入れ替わる", () => {
    const a = { entries: [{ id: 1 }], startedAt: "A" };
    const b = { entries: [{ id: 2 }], startedAt: "B" };
    expect(mergeFinalPositions([a, b])["entries"]).toEqual([{ id: 1 }, { id: 2 }]);
    expect(mergeFinalPositions([b, a])["entries"]).toEqual([{ id: 2 }, { id: 1 }]);
    expect(mergeFinalPositions([b, a])["startedAt"]).toBe("B");
  });

  it("entries が無い・0 件なら止まる", () => {
    expect(() => mergeFinalPositions([])).toThrow(DeliverArgError);
    expect(() => mergeFinalPositions([{ kind: "final_positions" }])).toThrow(DeliverArgError);
  });
});

describe("reportDataDirEnv", () => {
  it("組の report を組の順でカンマ区切りにする", () => {
    const groups = groupListOf(
      argsOf([
        "--group-work",
        "/w/a",
        "--group-time-limit-sec",
        "180",
        "--group-work",
        "/w/now",
        "--group-time-limit-sec",
        "180",
      ]),
    );
    expect(reportDataDirEnv(groups)).toBe("/w/a/report,/w/now/report");
  });
});

describe("timeCauseCommand", () => {
  it("全組を組の順に。--whatif-v2-dir は whatif-v2/ がある組だけ", () => {
    const groups = [
      groupPaths({ work: "/w/a", timeLimitSec: 180 }, "p2"),
      groupPaths({ work: "/w/b", timeLimitSec: 600 }, "p2"),
    ];
    const probe = fakeProbe({ jsonlDirs: ["/w/b/p2/whatif-v2"] });
    expect(timeCauseCommand(groups, probe, "/o/tc.json")).toEqual([
      "--kifu-dir",
      "/w/a/p2/kifu",
      "--patient",
      "/w/a/report/patient_report_data.json",
      "--time-limit-sec",
      "180",
      "--kifu-dir",
      "/w/b/p2/kifu",
      "--patient",
      "/w/b/report/patient_report_data.json",
      "--time-limit-sec",
      "600",
      "--whatif-v2-dir",
      "/w/b/p2/whatif-v2",
      "--out",
      "/o/tc.json",
    ]);
  });
});

describe("timeSearchCommand", () => {
  it("発見用 = 前回の組・検証用 = 今回の組。--outcomes は渡さない", () => {
    const prev = groupPaths({ work: "/w/prev", timeLimitSec: 180 }, "p2");
    const now = groupPaths({ work: "/w/now", timeLimitSec: 180 }, "p2");
    const probe = fakeProbe({ jsonlDirs: ["/w/prev/p2/whatif-v2", "/w/now/p2/whatif-v2"] });
    const flags = timeSearchCommand(prev, now, probe, "/o/ts.json");
    expect(flags).toEqual([
      "--role",
      "discover",
      "--kifu-dir",
      "/w/prev/p2/kifu",
      "--records-dir",
      "/w/prev/p2/stage2",
      "--time-limit-sec",
      "180",
      "--whatif-v2-dir",
      "/w/prev/p2/whatif-v2",
      "--role",
      "validate",
      "--kifu-dir",
      "/w/now/p2/kifu",
      "--records-dir",
      "/w/now/p2/stage2",
      "--time-limit-sec",
      "180",
      "--whatif-v2-dir",
      "/w/now/p2/whatif-v2",
      "--out",
      "/o/ts.json",
    ]);
    expect(flags).not.toContain("--outcomes");
  });
});

describe("renderTimeCauseCommand", () => {
  it("--search は探索があるときだけ", () => {
    expect(renderTimeCauseCommand("/o/tc.json", "/o/a4.pdf", undefined)).toEqual(["/o/tc.json", "/o/a4.pdf"]);
    expect(renderTimeCauseCommand("/o/tc.json", "/o/a4.pdf", "/o/ts.json")).toEqual(["/o/tc.json", "/o/a4.pdf", "--search", "/o/ts.json"]);
  });
});

// ---- check_answer.py / render_answer.py の材料の旗(run_check.sh の並び) ----

describe("answerMaterialFlags", () => {
  const args = argsOf([
    "--previous-work",
    "/w/prev",
    "--group-work",
    "/w/prev",
    "--group-time-limit-sec",
    "180",
    "--group-work",
    "/w/now",
    "--group-time-limit-sec",
    "180",
    "--group-work",
    "/w/long",
    "--group-time-limit-sec",
    "600",
  ]);
  const groups = groupListOf(args);
  const out = deliverOutPaths("/w/out");
  // 固定材料と同じ形: read/ は今回・10 分の組だけ(前回は whatif-v2 があっても read/ が無い)。
  const probe = fakeProbe({
    jsonlDirs: ["/w/now/p2/read", "/w/long/p2/read", "/w/prev/p2/whatif-v2", "/w/now/p2/whatif-v2", "/w/long/p2/whatif-v2"],
    files: ["/w/long/report/whatif_report_data.json", "/w/long/report/whatif.pdf", "/w/now/p2/type-summary.json", "/w/long/p2/type-summary.json"],
  });
  const flags = answerMaterialFlags(groups, probe, out, materialPlanOf(args));

  it("旗の並びと回数が run_check.sh と同じ(patient×3・prose×1・whatif-data×2・whatif-v2-dir×2・read-dir×2・type-summary×2・whatif-pdf×2・direct×2・time-cause・time-search・menu)", () => {
    const counts = (flag: string): number => flags.filter((t) => t === flag).length;
    expect(counts("--patient")).toBe(3);
    expect(counts("--time-limit-sec")).toBe(3);
    expect(counts("--prose")).toBe(1);
    expect(counts("--whatif-data")).toBe(2);
    expect(counts("--whatif-v2-dir")).toBe(2);
    expect(counts("--read-dir")).toBe(2);
    expect(counts("--type-summary")).toBe(2);
    expect(counts("--whatif-pdf")).toBe(2);
    expect(counts("--direct")).toBe(2);
    expect(counts("--time-cause")).toBe(1);
    expect(counts("--time-search")).toBe(1);
    expect(counts("--menu")).toBe(1);
  });

  it("prose は今回の組(--work)の 1 本だけ、patient と同じフォルダ(<work>/report/prose.json)を渡す(局番号は組ごとに 1 から振られ、納品される付録 1 は今回の組の本編だけのため)", () => {
    const proses = flags.map((t, i) => (flags[i - 1] === "--prose" ? t : null)).filter((t): t is string => t !== null);
    expect(proses).toEqual(["/w/now/report/prose.json"]);
  });

  it("whatif-data-now は今回の組(--work)の 1 本だけ(検査 7・付録 2 の材料。納品される付録 2 は今回の組のデータだけのため、2026-09-25 の直し・凍結の例外 7a)、whatif-data の本数は変わらない(全組・検査 1 の数の材料)", () => {
    const whatifDataNows = flags.map((t, i) => (flags[i - 1] === "--whatif-data-now" ? t : null)).filter((t): t is string => t !== null);
    expect(whatifDataNows).toEqual(["/w/now/report/whatif_report_data.json"]);
    expect(flags.filter((t) => t === "--whatif-data").length).toBe(2);
  });

  it("read/ が無い組には --whatif-v2-dir も --read-dir も渡さない(M4 の数が変わるため)", () => {
    expect(flags).not.toContain("/w/prev/p2/whatif-v2");
    expect(flags).not.toContain("/w/prev/p2/read");
    expect(flags).toContain("/w/now/p2/whatif-v2");
    expect(flags).toContain("/w/long/p2/whatif-v2");
  });

  it("patient は組の順に並ぶ(秒は各 patient の直後)", () => {
    const patients = flags.map((t, i) => (flags[i - 1] === "--patient" ? t : null)).filter((t): t is string => t !== null);
    expect(patients).toEqual(["/w/prev/report/patient_report_data.json", "/w/now/report/patient_report_data.json", "/w/long/report/patient_report_data.json"]);
    expect(flags[flags.indexOf("/w/long/report/patient_report_data.json") + 1]).toBe("--time-limit-sec");
    expect(flags[flags.indexOf("/w/long/report/patient_report_data.json") + 2]).toBe("600");
  });

  it("今回の組の whatif-data・whatif-pdf は、まだファイルが無くても渡す(段 3 が作るため)", () => {
    expect(flags).toContain("/w/now/report/whatif_report_data.json");
    expect(flags).toContain("/w/now/report/whatif.pdf");
  });

  it("付録 3 の PDF も --whatif-pdf に渡す(検査 2 の照合)", () => {
    expect(flags).toContain(out.appendix3);
  });

  it("--whatif-pdf は今回の組の whatifPdf と付録 3 の 2 本だけで、他の組の whatifPdf は含まない(納品される付録 2 は今回の組のデータだけのため、2026-09-25 の直し・凍結の例外 7c)", () => {
    expect(flags.filter((t) => t === "--whatif-pdf").length).toBe(2);
    const whatifPdfs = flags.map((t, i) => (flags[i - 1] === "--whatif-pdf" ? t : null)).filter((t): t is string => t !== null);
    expect(whatifPdfs).toEqual(["/w/now/report/whatif.pdf", out.appendix3]);
    expect(flags).not.toContain("/w/prev/report/whatif.pdf");
    expect(flags).not.toContain("/w/long/report/whatif.pdf");
  });

  it("--time-search は --previous-work があるときだけ", () => {
    const solo = argsOf();
    expect(answerMaterialFlags(groupListOf(solo), fakeProbe({}), out, materialPlanOf(solo))).not.toContain("--time-search");
  });

  it("check-answer は md が先頭、render-answer は md → PDF が先頭で、残りは同じ", () => {
    const plan = materialPlanOf(args);
    const check = checkAnswerCommand(groups, probe, out, plan);
    const render = renderAnswerCommand(groups, probe, out, plan);
    expect(check[0]).toBe(out.answerDraft);
    expect(render.slice(0, 2)).toEqual([out.answerDraft, out.answerPdf]);
    expect(check.slice(1)).toEqual(render.slice(2));
  });

  it("answer_facts は --name を先頭に、menu・whatif-pdf・prose は渡さない(answer_facts.py は --prose を知らない)", () => {
    const facts = answerFactsCommand(groups, probe, out, "お客さま", materialPlanOf(args));
    expect(facts.slice(0, 2)).toEqual(["--name", "お客さま"]);
    expect(facts).not.toContain("--menu");
    expect(facts).not.toContain("--prose");
    expect(facts).not.toContain("--whatif-pdf");
    expect(facts.slice(-2)).toEqual(["--out", out.answerDraft]);
  });

  it("answer_facts は --whatif-data-now も渡さない(answer_facts.py は知らない。検査 7 は check_answer.py/render_answer.py だけの機能)", () => {
    const facts = answerFactsCommand(groups, probe, out, "お客さま", materialPlanOf(args));
    expect(facts).not.toContain("--whatif-data-now");
  });
});

describe("checkDeliveryCommand", () => {
  it("フォルダ + --forbid の繰り返し", () => {
    expect(checkDeliveryCommand("/w/out", ["甲", "乙"])).toEqual(["/w/out", "--forbid", "甲", "--forbid", "乙"]);
  });
});

// ---- 納品ログ・段の順 ----

describe("deliverLogLineOf", () => {
  it("1 行 1 段の JSON(rc は数か skip)", () => {
    expect(deliverLogLineOf({ stage: "answer-check", startedAt: "A", finishedAt: "B", rc: 0, humanGate: false })).toBe(
      '{"stage":"answer-check","startedAt":"A","finishedAt":"B","rc":0,"humanGate":false}\n',
    );
    expect(deliverLogLineOf({ stage: "prose-gate", startedAt: "A", finishedAt: "B", rc: "skip", humanGate: true })).toContain('"rc":"skip"');
  });
});

describe("deliverLogArgsLineOf(P-168 (ウ))", () => {
  it("再開に要る 7 つだけを書く(`--name`・`--title`・`--forbid` は書かない)", () => {
    const line = deliverLogArgsLineOf(argsOf(["--group-label", "3 分切れ負け", "--forbid", "禁じる語"]), "2026-09-29T10:00:00.000Z");
    const entry = JSON.parse(line) as Record<string, unknown>;
    // **鍵を列挙で見る** ― 「名前が無いこと」だけを見ると、後から別の鍵が増えても通る。
    expect(Object.keys(entry).sort()).toEqual(
      ["groupLabel", "kifuDir", "out", "person", "timeLimitSec", "today", "work", "kind", "writtenAt"].sort(),
    );
    expect(entry.person).toBe("p2");
    expect(entry.groupLabel).toBe("3 分切れ負け");
    expect(line.endsWith("\n")).toBe(true);
  });

  it("名前を渡す引数の値が 1 つも行に出ない", () => {
    // `--name`・`--title`・`--forbid` に渡した値そのものを探す ―
    // 鍵の名前を変えて中身だけ残す直しが入っても落ちる。
    const line = deliverLogArgsLineOf(argsOf(["--forbid", "禁じる語"]), "2026-09-29T10:00:00.000Z");
    for (const value of ["お客さま", "題", "禁じる語"]) {
      expect(line).not.toContain(value);
    }
  });

  it("`--group-label` を渡さなければ鍵自体が付かない", () => {
    const entry = JSON.parse(deliverLogArgsLineOf(argsOf(), "t")) as Record<string, unknown>;
    expect("groupLabel" in entry).toBe(false);
  });

  it("deliver.ts が本当に呼んでいる(段の繰り返しより前で、1 回だけ)", () => {
    // **呼び出しを消しても試験が黙る**のを防ぐ(2026-09-29 に同じ型で当たった ―
    // `check_no_real_name` の呼び出しを外したとき、字面の試験が `def` の行に当たって通った)。
    // `deliver.ts` は副作用の本体(`run()`)を輸出しないので、**原文で位置を見る**。
    const src = readFileSync(new URL("../deliver.ts", import.meta.url), "utf-8");
    const calls = src.match(/^ {2}appendFileSync\(out\.log, deliverLogArgsLineOf\(/gm) ?? [];
    expect(calls.length).toBe(1);
    expect(src.indexOf("appendFileSync(out.log, deliverLogArgsLineOf(")).toBeLessThan(
      src.indexOf("for (const stage of initialSteps.map"),
    );
  });

  it("段の行を読む側(seatSecondsOf)は、この行を飛ばす", () => {
    // 引数の行に `stage` が無いので、段ごとの読みには混ざらない(**混ざると席の時間が壊れる**)。
    const argsLine = deliverLogArgsLineOf(argsOf(), "2026-09-29T10:00:00.000Z");
    const lines = [
      argsLine.trimEnd(),
      JSON.stringify({ stage: "exit-gate", startedAt: "a", finishedAt: "2026-09-29T10:00:00.000Z", rc: 1, humanGate: true }),
    ];
    expect(seatSecondsOf(lines, "exit-gate", "2026-09-29T10:00:30.000Z")).toBe(30);
  });
});

describe("PERSON_REFERENT(P-174 (ウ))", () => {
  it("pipeline へ渡す引数に、名前として渡された値が 1 つも出ない", () => {
    // **値そのものを探す。**鍵の名前を変えて中身だけ残す直しが入っても落ちる。
    const args = argsOf();
    const flat = pipelineCommand(args, "pdf").join("\u0000");
    expect(flat).not.toContain(args.name);
    expect(pipelineCommand(args, "pdf")).toContain(PERSON_REFERENT);
  });

  it("陽性対照: 実名を渡しても pipeline の引数には出ない", () => {
    //  の土台が既に `--name` を持つので、**土台ごと置き換える**(同じ旗は 2 回渡せない)。
    const args = parseDeliverArgs(BASE_ARGV.map((v) => (v === "お客さま" ? "実名テスト" : v)));
    expect(args.name).toBe("実名テスト");
    expect(pipelineCommand(args, "pdf").join("\u0000")).not.toContain("実名テスト");
  });

  it("`--title` は触っていない(司令塔の条件 ― 直すのは `--name` の 1 か所だけ)", () => {
    const args = argsOf();
    expect(pipelineCommand(args, "pdf")).toContain(args.title);
  });

  it("`exit_body.py` の既定と同じ語(呼び方の出どころを 2 つにしない)", () => {
    // TS と python で定数を共有できないので、**python の既定を読んで一致を見る**。
    const src = readFileSync(new URL("../report-pdf/exit_body.py", import.meta.url), "utf-8");
    expect(src).toContain(`"person": "${PERSON_REFERENT}"`);
  });
});

describe("stagesFrom", () => {
  it("--from が無ければ全段、あればその段から", () => {
    expect(stagesFrom(undefined)).toEqual([...DELIVER_STAGES]);
    // 顧客向け出口の 4 段が入った(2026-09-29)。**最後の段は `exit-send`**(C-1b。2026-09-30)。
    // **⑤ の門 `exit-select` が `exit-candidates` の直前に入った**(2026-10-01。司令塔の GO)。
    // `exit-draft` は `exit-select` の**直前**に入った(S-3。2026-10-06)。
    expect(stagesFrom("answer-check")).toEqual([
      "answer-check", "answer-pdf",
      "exit-draft",
      "exit-select",
      // ⑥ `exit-fill` は候補の直後・門の直前(2026-10-05)。
      "exit-candidates", "exit-fill", "exit-gate", "exit-render", "exit-check",
      "check-delivery", "exit-send",
    ]);
  });

  it("--from pipeline-gate は最初の段(= 全段)", () => {
    expect(stagesFrom("pipeline-gate")).toEqual([...DELIVER_STAGES]);
    expect(stagesFrom("pipeline-gate")[0]).toBe("pipeline-gate");
  });
});

// ---- 段の一覧(planDeliver) ----

describe("planDeliver", () => {
  const args = argsOf([
    "--previous-work",
    "/w/prev",
    "--group-work",
    "/w/prev",
    "--group-time-limit-sec",
    "180",
    "--group-work",
    "/w/now",
    "--group-time-limit-sec",
    "180",
    "--group-work",
    "/w/long",
    "--group-time-limit-sec",
    "600",
  ]);
  const probe = fakeProbe({
    jsonlDirs: ["/w/now/p2/read", "/w/long/p2/read", "/w/prev/p2/whatif-v2", "/w/now/p2/whatif-v2", "/w/long/p2/whatif-v2"],
    files: ["/w/now/report/prose.json"],
    fixed: { "/w/prev/p2/kifu": ["/w/prev/p2/kifu/a.fixed.json"], "/w/now/p2/kifu": ["/w/now/p2/kifu/b.fixed.json"] },
    losses: { "/w/prev/report/patient_report_data.json": 2, "/w/now/report/patient_report_data.json": 1 },
  });
  const steps = planDeliver(args, probe, (t) => `cmd:${t}`);

  it("計画の順どおり(段 pipeline-gate が先頭。⑤ の門を入れて 23 段)", () => {
    expect(steps.map((s) => s.stage)).toEqual([...DELIVER_STAGES]);
    expect(steps[0]!.stage).toBe("pipeline-gate");
    expect(steps[1]!.stage).toBe("pipeline-data");
    expect(steps.map((s) => s.stage).indexOf("pipeline-gate")).toBeLessThan(steps.map((s) => s.stage).indexOf("pipeline-data"));
  });

  it("prose.json があれば prose-gate は skip、answer-gate は常に確認点", () => {
    expect(steps.find((s) => s.stage === "prose-gate")!.action).toBe("skip");
    expect(steps.find((s) => s.stage === "answer-gate")!.action).toBe("gate");
    expect(steps.find((s) => s.stage === "answer-gate")!.reason).toContain(TODO_MARK);
  });

  it("finalPositions は全組ぶんの引数を組の順に並べる(0 局の組を飛ばす判定は実行時)", () => {
    const step = steps.find((s) => s.stage === "appendix3-final")!;
    expect(step.args.filter((t) => t === "--kifu")).toHaveLength(3);
    // 部分ファイルは組の順(1・2・3)で、その順にしか現れない
    const positions = [0, 1, 2].map((i) => step.args.indexOf(finalPositionsPartPath("/w/out", i)));
    expect(positions.every((p) => p >= 0)).toBe(true);
    expect(positions).toEqual([...positions].sort((a, b) => a - b));
    // patient も組の順
    const patients = step.args.map((t, i) => (step.args[i - 1] === "--patient" ? t : null)).filter((t): t is string => t !== null);
    expect(patients).toEqual(["/w/prev/report/patient_report_data.json", "/w/now/report/patient_report_data.json", "/w/long/report/patient_report_data.json"]);
    expect(step.reason).toContain("実行時に飛ばす");
  });

  it("付録 3 の PDF は REPORT_DATA_DIR を組の順で渡す", () => {
    const step = steps.find((s) => s.stage === "appendix3-pdf")!;
    expect(step.env).toEqual({ REPORT_DATA_DIR: "/w/prev/report,/w/now/report" + ",/w/long/report" });
  });

  it("--previous-work が無ければ探索の段は skip、付録 4 に --search を渡さない", () => {
    const solo = argsOf();
    const soloSteps = planDeliver(solo, fakeProbe({}), (t) => t);
    expect(soloSteps.find((s) => s.stage === "appendix4-search")!.action).toBe("skip");
    expect(soloSteps.find((s) => s.stage === "appendix4-pdf")!.args).not.toContain("--search");
  });

  it("--from はその段から先だけを組む", () => {
    const resumed = planDeliver(argsOf(["--from", "answer-check"]), probe, (t) => t);
    expect(resumed.map((s) => s.stage)).toEqual([
      "answer-check", "answer-pdf",
      // S-3(2026-10-06)。`exit-draft` は `exit-select` の直前。
      "exit-draft",
      // ⑤ の門(2026-10-01)。**`exit-candidates` の直前**。⑥ は候補の直後(2026-10-05)。
      "exit-select",
      "exit-candidates", "exit-fill", "exit-gate", "exit-render", "exit-check",
      "check-delivery", "exit-send",
    ]);
  });

  // 【fixture だけの追記(凍結の例外 10 件目。PDF_DONE3_BRIEF.md §5)】期待値(9 段すべて skip)は変えない。
  // deliverables-pdf・appendix3-pdf・appendix4-pdf が mtime を見るようになったため、
  // 入力(work の 3 冊・direct の 4 つの JSON)を 100、出力(顧客フォルダの 3 冊・付録 3・付録 4 の PDF)を 200 にする。
  // work の 3 冊は `files` にも足す(`probe.exists` は見ないが、実物に近づけるため)。
  it("出力が既にあれば skip(済みの判定)", () => {
    const done = fakeProbe({
      files: [
        "/w/now/report/prose.json",
        "/w/now/report/front.pdf",
        "/w/now/report/main.pdf",
        "/w/now/report/whatif.pdf",
        "/w/out/1_まとめ.pdf",
        "/w/out/2_付録1_形勢が動いた対局.pdf",
        "/w/out/3_付録2_分かれ道.pdf",
        "/w/out/direct/direct_answers.json",
        "/w/out/direct/final_positions.json",
        "/w/out/5_付録3_直接の答え.pdf",
        "/w/out/direct/time_cause.json",
        "/w/out/direct/time_cause_search.json",
        "/w/out/6_付録4_時間の使い方.pdf",
        "/w/out/direct/answer_menu.json",
        "/w/out/8_B_どうしたら_下書き.md",
        "/w/out/8_B_どうしたら.pdf",
      ],
      mtimes: {
        // 入力
        "/w/now/report/front.pdf": 100,
        "/w/now/report/main.pdf": 100,
        "/w/now/report/whatif.pdf": 100,
        "/w/out/direct/direct_answers.json": 100,
        "/w/out/direct/final_positions.json": 100,
        "/w/out/direct/time_cause.json": 100,
        "/w/out/direct/time_cause_search.json": 100,
        // 出力
        "/w/out/1_まとめ.pdf": 200,
        "/w/out/2_付録1_形勢が動いた対局.pdf": 200,
        "/w/out/3_付録2_分かれ道.pdf": 200,
        "/w/out/5_付録3_直接の答え.pdf": 200,
        "/w/out/6_付録4_時間の使い方.pdf": 200,
      },
    });
    const byStage = new Map(planDeliver(args, done, (t) => t).map((s) => [s.stage, s.action]));
    for (const stage of [
      "deliverables-pdf",
      "appendix3-answers",
      "appendix3-final",
      "appendix3-pdf",
      "appendix4-cause",
      "appendix4-search",
      "appendix4-pdf",
      "answer-menu",
      "answer-draft",
    ] as const) {
      expect(byStage.get(stage), stage).toBe("skip");
    }
  });

  // answer-pdf の済みの判定(凍結の例外 9 件目。ANSWERPDF_DONE_BRIEF.md §2)。
  // 存在だけでなく、B の PDF が B の md(`out.answerDraft`)より新しいかを見る(`pipeline.ts` の `pdfDone` と同じ考え方)。
  describe("answer-pdf の済みの判定(mtime 比較)", () => {
    const solo = argsOf();
    const out = deliverOutPaths("/w/out");

    it("md の mtime > PDF の mtime(md を後から直した)→ run(§2 の 1)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ files: [out.answerDraft, out.answerPdf], mtimes: { [out.answerDraft]: 200, [out.answerPdf]: 100 } }),
        (t) => t,
      ).find((s) => s.stage === "answer-pdf")!;
      expect(step.action).toBe("run");
    });

    it("PDF の mtime > md の mtime → skip(§2 の 2)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ files: [out.answerDraft, out.answerPdf], mtimes: { [out.answerDraft]: 100, [out.answerPdf]: 200 } }),
        (t) => t,
      ).find((s) => s.stage === "answer-pdf")!;
      expect(step.action).toBe("skip");
    });

    it("PDF が無い → run(§2 の 3)", () => {
      const step = planDeliver(solo, fakeProbe({ files: [out.answerDraft], mtimes: { [out.answerDraft]: 100 } }), (t) => t).find(
        (s) => s.stage === "answer-pdf",
      )!;
      expect(step.action).toBe("run");
    });

    it("md の mtime が読めない(無い)→ run(作る側に倒す。§2 の 3)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ files: [out.answerPdf], mtimes: { [out.answerPdf]: 200 } }),
        (t) => t,
      ).find((s) => s.stage === "answer-pdf")!;
      expect(step.action).toBe("run");
    });

    // 変異 2(§3(D)の 2。`>=` にする変異を落とすために追加。同時刻は「済み」ではなく作る側に倒す)。
    it("PDF の mtime と md の mtime が同じ → run(同時刻は済みにしない)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ files: [out.answerDraft, out.answerPdf], mtimes: { [out.answerDraft]: 100, [out.answerPdf]: 100 } }),
        (t) => t,
      ).find((s) => s.stage === "answer-pdf")!;
      expect(step.action).toBe("run");
    });
  });

  // deliverables-pdf(copyDone)・appendix3-pdf(a3PdfDone)・appendix4-pdf(a4PdfDone)の済みの判定
  // (凍結の例外 10 件目。PDF_DONE3_BRIEF.md §2)。answer-pdf(例外 9 件目)と同じ考え方 ―
  // 出力とすべての入力の mtime が読めて、出力がすべての入力より新しいときだけ済み。
  describe("deliverables-pdf の済みの判定(mtime 比較。凍結の例外 10 件目)", () => {
    const solo = argsOf();
    const out = deliverOutPaths("/w/out");
    const work = groupPaths({ work: "/w/now", timeLimitSec: 180 }, "p2");

    it("3 冊とも work の版が複製先より新しい → run(§2 の a)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({
          mtimes: {
            [work.frontPdf]: 200,
            [out.front]: 100,
            [work.mainPdf]: 200,
            [out.main]: 100,
            [work.whatifPdf]: 200,
            [out.whatif]: 100,
          },
        }),
        (t) => t,
      ).find((s) => s.stage === "deliverables-pdf")!;
      expect(step.action).toBe("run");
    });

    it("3 冊とも複製先が work の版より新しい → skip(§2 の b)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({
          mtimes: {
            [work.frontPdf]: 100,
            [out.front]: 200,
            [work.mainPdf]: 100,
            [out.main]: 200,
            [work.whatifPdf]: 100,
            [out.whatif]: 200,
          },
        }),
        (t) => t,
      ).find((s) => s.stage === "deliverables-pdf")!;
      expect(step.action).toBe("skip");
    });

    it("複製先の mtime が読めない(無い)→ run(§2 の c)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({
          mtimes: { [work.frontPdf]: 100, [work.mainPdf]: 100, [work.whatifPdf]: 100 },
        }),
        (t) => t,
      ).find((s) => s.stage === "deliverables-pdf")!;
      expect(step.action).toBe("run");
    });

    it("work 側の 1 冊の mtime が読めない → run(§2 の d)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({
          mtimes: {
            [out.front]: 200,
            [out.main]: 200,
            [out.whatif]: 200,
            [work.mainPdf]: 100,
            [work.whatifPdf]: 100,
            // work.frontPdf は与えない(読めない)
          },
        }),
        (t) => t,
      ).find((s) => s.stage === "deliverables-pdf")!;
      expect(step.action).toBe("run");
    });

    it("3 組のうち 1 組だけ src(work の版)が新しい → run(§2 の g)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({
          mtimes: {
            [work.frontPdf]: 200,
            [out.front]: 100, // この組だけ work の版が新しい
            [work.mainPdf]: 100,
            [out.main]: 200,
            [work.whatifPdf]: 100,
            [out.whatif]: 200,
          },
        }),
        (t) => t,
      ).find((s) => s.stage === "deliverables-pdf")!;
      expect(step.action).toBe("run");
    });

    // 変異 3(§3(D)の 3。`>=` にする変異を落とすために追加。同時刻は「済み」ではなく作る側に倒す)。
    it("複製先と work の版が同時刻 → run(同時刻は済みにしない)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({
          mtimes: {
            [work.frontPdf]: 100,
            [out.front]: 100,
            [work.mainPdf]: 100,
            [out.main]: 100,
            [work.whatifPdf]: 100,
            [out.whatif]: 100,
          },
        }),
        (t) => t,
      ).find((s) => s.stage === "deliverables-pdf")!;
      expect(step.action).toBe("run");
    });
  });

  describe("appendix3-pdf の済みの判定(mtime 比較。凍結の例外 10 件目)", () => {
    const solo = argsOf();
    const out = deliverOutPaths("/w/out");

    it("入力(direct_answers・final_positions)が付録 3 の PDF より新しい → run(§2 の a)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ mtimes: { [out.appendix3]: 100, [out.directAnswers]: 200, [out.finalPositions]: 50 } }),
        (t) => t,
      ).find((s) => s.stage === "appendix3-pdf")!;
      expect(step.action).toBe("run");
    });

    it("付録 3 の PDF が両方の入力より新しい → skip(§2 の b)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ mtimes: { [out.appendix3]: 300, [out.directAnswers]: 100, [out.finalPositions]: 200 } }),
        (t) => t,
      ).find((s) => s.stage === "appendix3-pdf")!;
      expect(step.action).toBe("skip");
    });

    it("付録 3 の PDF の mtime が読めない(無い)→ run(§2 の c)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ mtimes: { [out.directAnswers]: 100, [out.finalPositions]: 100 } }),
        (t) => t,
      ).find((s) => s.stage === "appendix3-pdf")!;
      expect(step.action).toBe("run");
    });

    it("入力の 1 つ(final_positions)の mtime が読めない → run(§2 の d)", () => {
      const step = planDeliver(solo, fakeProbe({ mtimes: { [out.appendix3]: 300, [out.directAnswers]: 100 } }), (t) => t).find(
        (s) => s.stage === "appendix3-pdf",
      )!;
      expect(step.action).toBe("run");
    });

    // 変異 3(§3(D)の 3。`>=` にする変異を落とすために追加。同時刻は「済み」ではなく作る側に倒す)。
    it("付録 3 の PDF と入力が同時刻 → run(同時刻は済みにしない)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ mtimes: { [out.appendix3]: 100, [out.directAnswers]: 100, [out.finalPositions]: 100 } }),
        (t) => t,
      ).find((s) => s.stage === "appendix3-pdf")!;
      expect(step.action).toBe("run");
    });
  });

  describe("appendix4-pdf の済みの判定(mtime 比較。凍結の例外 10 件目)", () => {
    const solo = argsOf();
    const withPrev = argsOf(["--previous-work", "/w/prev"]);
    const out = deliverOutPaths("/w/out");

    it("入力(time_cause)が付録 4 の PDF より新しい → run(§2 の a)", () => {
      const step = planDeliver(solo, fakeProbe({ mtimes: { [out.appendix4]: 100, [out.timeCause]: 200 } }), (t) => t).find(
        (s) => s.stage === "appendix4-pdf",
      )!;
      expect(step.action).toBe("run");
    });

    it("付録 4 の PDF が time_cause より新しい → skip(§2 の b)", () => {
      const step = planDeliver(solo, fakeProbe({ mtimes: { [out.appendix4]: 200, [out.timeCause]: 100 } }), (t) => t).find(
        (s) => s.stage === "appendix4-pdf",
      )!;
      expect(step.action).toBe("skip");
    });

    it("付録 4 の PDF の mtime が読めない(無い)→ run(§2 の c)", () => {
      const step = planDeliver(solo, fakeProbe({ mtimes: { [out.timeCause]: 100 } }), (t) => t).find((s) => s.stage === "appendix4-pdf")!;
      expect(step.action).toBe("run");
    });

    it("time_cause の mtime が読めない → run(§2 の d)", () => {
      const step = planDeliver(solo, fakeProbe({ mtimes: { [out.appendix4]: 200 } }), (t) => t).find((s) => s.stage === "appendix4-pdf")!;
      expect(step.action).toBe("run");
    });

    it("hasSearch でなく time_cause_search が無く、出力が time_cause より新しい → skip(見てはいけない入力を見ていないことの証明。§2 の e)", () => {
      const step = planDeliver(
        solo,
        fakeProbe({ mtimes: { [out.appendix4]: 250, [out.timeCause]: 120 } }), // out.timeSearch は与えない
        (t) => t,
      ).find((s) => s.stage === "appendix4-pdf")!;
      expect(step.action).toBe("skip");
    });

    it("hasSearch で time_cause_search が付録 4 の PDF より新しい → run(§2 の f)", () => {
      const step = planDeliver(
        withPrev,
        fakeProbe({ mtimes: { [out.appendix4]: 200, [out.timeCause]: 100, [out.timeSearch]: 300 } }),
        (t) => t,
      ).find((s) => s.stage === "appendix4-pdf")!;
      expect(step.action).toBe("run");
    });

    // 変異 3(§3(D)の 3。`>=` にする変異を落とすために追加。同時刻は「済み」ではなく作る側に倒す)。
    it("付録 4 の PDF と time_cause が同時刻 → run(同時刻は済みにしない)", () => {
      const step = planDeliver(solo, fakeProbe({ mtimes: { [out.appendix4]: 100, [out.timeCause]: 100 } }), (t) => t).find(
        (s) => s.stage === "appendix4-pdf",
      )!;
      expect(step.action).toBe("run");
    });
  });

  // 段ごとに計画を読み直す(REPLAN_BRIEF.md §2.1・§2.4)。
  //
  // 【断ってあること】これは `planDeliver` を複数回呼んだときの振る舞いだけを測る ― `deliver.ts`(CLI)の
  // 輪の中で「段の直前に呼び直す」1 行そのものは、この試験では守れない(P-32 と同じ型)。
  describe("段の直前に計画を読み直す(§2.4 の 1・2)", () => {
    it("probe の答えが呼ばれるたびに変わる(1 回目=材料無し・2 回目以降=材料あり)と、§1 の表の 6 段すべてで欠けていた旗が入る", () => {
      let ready = false;
      const growingProbe: DeliverProbe = {
        exists: (p) => ready && p === "/w/now/p2/type-summary.json",
        hasJsonl: (d) => ready && (d === "/w/now/p2/read" || d === "/w/now/p2/whatif-v2"),
        fixedKifuFiles: (d) => (ready && d === "/w/now/p2/kifu" ? ["/w/now/p2/kifu/a.fixed.json"] : []),
        timeUpLossCount: () => 0,
        mtimeMs: () => undefined,
      };
      const solo = argsOf();

      const before = planDeliver(solo, growingProbe, (t) => t);
      ready = true; // 「後の段が作った材料が見える」の模型(materialsPresent という 1 回目とは別の答えを返す)
      const after = planDeliver(solo, growingProbe, (t) => t);

      const find = (steps: typeof before, stage: string) => steps.find((s) => s.stage === stage)!;

      // appendix3-answers(direct-answers): --whatif-v2-dir・--read-dir・--time-limit-sec
      expect(find(before, "appendix3-answers").args).toEqual(["--out", "/w/out/direct/direct_answers.json"]);
      expect(find(after, "appendix3-answers").args).toEqual(["--whatif-v2-dir", "/w/now/p2/whatif-v2", "--read-dir", "/w/now/p2/read", "--time-limit-sec", "180", "--out", "/w/out/direct/direct_answers.json"]);

      // appendix3-final(final-positions): --kifu のファイル一覧が空でなくなる
      const beforeFinal = find(before, "appendix3-final").args;
      const afterFinal = find(after, "appendix3-final").args;
      expect(beforeFinal[beforeFinal.indexOf("--kifu") + 1]).toBe("--patient"); // 空(次の旗が続く)
      expect(afterFinal[afterFinal.indexOf("--kifu") + 1]).toBe("/w/now/p2/kifu/a.fixed.json");

      // appendix4-cause(time-cause): --whatif-v2-dir
      expect(find(before, "appendix4-cause").args).not.toContain("--whatif-v2-dir");
      expect(find(after, "appendix4-cause").args).toContain("--whatif-v2-dir");

      // answer-draft(answer-facts): --whatif-v2-dir・--read-dir
      expect(find(before, "answer-draft").args).not.toContain("--read-dir");
      expect(find(after, "answer-draft").args).toEqual(expect.arrayContaining(["--whatif-v2-dir", "/w/now/p2/whatif-v2", "--read-dir", "/w/now/p2/read"]));

      // answer-check(check-answer): --whatif-v2-dir・--read-dir・--type-summary
      expect(find(before, "answer-check").args).not.toContain("--type-summary");
      expect(find(after, "answer-check").args).toEqual(
        expect.arrayContaining(["--whatif-v2-dir", "/w/now/p2/whatif-v2", "--read-dir", "/w/now/p2/read", "--type-summary", "/w/now/p2/type-summary.json"]),
      );

      // answer-pdf(render-answer): --whatif-v2-dir・--read-dir・--type-summary(answer-check と同じ材料)
      expect(find(before, "answer-pdf").args).not.toContain("--type-summary");
      expect(find(after, "answer-pdf").args).toEqual(
        expect.arrayContaining(["--whatif-v2-dir", "/w/now/p2/whatif-v2", "--read-dir", "/w/now/p2/read", "--type-summary", "/w/now/p2/type-summary.json"]),
      );
    });

    it("材料が揃った probe では、planDeliver を何回呼んでも同じ計画が返る(冪等)", () => {
      const first = planDeliver(args, probe, (t) => t);
      for (let i = 0; i < 5; i += 1) {
        expect(planDeliver(args, probe, (t) => t)).toStrictEqual(first);
      }
    });
  });

  describe("materialsPending(§2.2)", () => {
    const readyProbe = fakeProbe({
      jsonlDirs: ["/w/now/p2/read", "/w/now/p2/whatif-v2"],
      fixed: { "/w/now/p2/kifu": ["/w/now/p2/kifu/a.fixed.json"] },
    });

    it("read/・whatif-v2/・固定棋譜がすべて揃っていれば false", () => {
      expect(materialsPending(argsOf(), readyProbe)).toBe(false);
    });

    it("read/ が無ければ true", () => {
      const probeNoRead = fakeProbe({ jsonlDirs: ["/w/now/p2/whatif-v2"], fixed: { "/w/now/p2/kifu": ["/w/now/p2/kifu/a.fixed.json"] } });
      expect(materialsPending(argsOf(), probeNoRead)).toBe(true);
    });

    it("whatif-v2/ が無ければ true", () => {
      const probeNoWhatif = fakeProbe({ jsonlDirs: ["/w/now/p2/read"], fixed: { "/w/now/p2/kifu": ["/w/now/p2/kifu/a.fixed.json"] } });
      expect(materialsPending(argsOf(), probeNoWhatif)).toBe(true);
    });

    it("固定棋譜(*.fixed.json)が無ければ true", () => {
      const probeNoFixed = fakeProbe({ jsonlDirs: ["/w/now/p2/read", "/w/now/p2/whatif-v2"] });
      expect(materialsPending(argsOf(), probeNoFixed)).toBe(true);
    });

    it("段 pipeline-data が --from で外れているときは false(材料が無くても注記しない)", () => {
      const probeNothing = fakeProbe({});
      expect(materialsPending(argsOf(["--from", "answer-check"]), probeNothing)).toBe(false);
    });
  });

  // 1 コマンド化(指示書 §3.2・§3.3・§3.5 の 2〜7)。
  describe("段 pipeline-gate", () => {
    const COMPARE = ["--compare-dir", "/c/a", "/c/b", "--compare-person", "p5"];
    const gateFile = "/w/now/p2/gate.jsonl";
    const gateStep = (extra: readonly string[], world: FakeWorld) =>
      planDeliver(argsOf(extra), fakeProbe(world), (t) => `cmd:${t}`).find((s) => s.stage === "pipeline-gate")!;

    it("gate.jsonl があれば skip(存在だけを見る)", () => {
      const step = gateStep(COMPARE, { files: [gateFile] });
      expect(step.action).toBe("skip");
      expect(step.reason).toContain(gateFile);
    });

    it("gate.jsonl が無くて compare があれば run で、引数は --until gate + compare だけ", () => {
      const step = gateStep(COMPARE, {});
      expect(step.action).toBe("run");
      expect(step.tool).toBe("pipeline");
      expect(step.args).toEqual([
        "--person",
        "p2",
        "--kifu-dir",
        "/w/kifu",
        "--work",
        "/w/now",
        "--until",
        "gate",
        "--compare-dir",
        "/c/a",
        "/c/b",
        "--compare-person",
        "p5",
      ]);
      for (const flag of ["--whatif", "--name", "--title", "--today", "--time-limit-sec", "--previous"]) {
        expect(step.args, flag).not.toContain(flag);
      }
    });

    it("gate.jsonl が無くて compare も無ければ fail(人間の確認点ではない)。何が要るかを書く", () => {
      const step = gateStep([], {});
      expect(step.action).toBe("fail");
      expect(step.args).toEqual([]);
      expect(step.reason).toContain(gateFile);
      expect(step.reason).toContain("--compare-dir");
      expect(step.reason).toContain("--compare-person");
    });

    it("compare は段 pipeline-data・pipeline-pdf へ渡らない(既存の段の引数は変わらない)", () => {
      const plain = planDeliver(argsOf(), probe, (t) => t);
      const withCompare = planDeliver(argsOf(COMPARE), probe, (t) => t);
      for (const stage of ["pipeline-data", "pipeline-pdf"] as const) {
        const before = plain.find((s) => s.stage === stage)!;
        const after = withCompare.find((s) => s.stage === stage)!;
        expect(after.args, stage).toEqual(before.args);
        expect(after.args, stage).not.toContain("--compare-dir");
        expect(after.args, stage).not.toContain("--compare-person");
        expect(after.args, stage).not.toContain("/c/a");
        expect(after.args, stage).not.toContain("p5");
      }
    });

    it("gate.jsonl があるときも、段 pipeline-data・pipeline-pdf の引数は pipelineCommand のまま", () => {
      const done = argsOf(COMPARE);
      const steps2 = planDeliver(done, fakeProbe({ files: [gateFile] }), (t) => t);
      expect(steps2.find((s) => s.stage === "pipeline-data")!.args).toEqual(pipelineCommand(done, "report-data"));
      expect(steps2.find((s) => s.stage === "pipeline-pdf")!.args).toEqual(pipelineCommand(done, "pdf"));
    });

    it("--from pipeline-gate で最初から組める", () => {
      const resumed = planDeliver(argsOf(["--from", "pipeline-gate", ...COMPARE]), probe, (t) => t);
      expect(resumed.map((s) => s.stage)).toEqual([...DELIVER_STAGES]);
    });
  });

  // 2026-09-23。指示書(KIFUNAME_BRIEF.md)§2.5。付録 4(report-pdf/render_time_cause.py)が
  // kifuId を数の照合にかけ、冊子に印字する不具合を入口で機械に見る検査。
  describe("kifuNameProblems", () => {
    it("固定の 8 個の値を固定する(report-pdf/render_time_cause.py:115 の GLOBAL_ALLOWED_NUMBERS の写し)", () => {
      expect(new Set(KIFU_NAME_FIXED_ALLOWED_NUMBERS)).toEqual(new Set([1, 2, 3, 4, 5, 9, 10, 300]));
    });

    it("tatsunami20 の実物の名前(20 件)は問題 0 件", () => {
      const files = [
        "kifu2-01-sente.kif",
        "kifu2-02-gote.kif",
        "kifu2-03-gote.kif",
        "kifu2-04-sente.kif",
        "kifu2-05-gote.kif",
        "kifu2-06-gote.kif",
        "kifu2-07-gote.kif",
        "kifu2-08-gote.kif",
        "kifu2-09-sente.kif",
        "kifu2-10-gote.kif",
        "kifu2-11-sente.kif",
        "kifu2-12-gote.kif",
        "kifu2-13-gote.kif",
        "kifu2-14-gote.kif",
        "kifu2-15-sente.kif",
        "kifu2-16-sente.kif",
        "kifu2-17-sente.kif",
        "kifu2-18-sente.kif",
        "kifu2-19-gote.kif",
        "kifu2-20-sente.kif",
      ];
      expect(kifuNameProblems("/kifu", files)).toEqual([]);
    });

    it("tatsunami3 の実物の名前(14 件)は問題 0 件", () => {
      const files = [
        "t3-01-sente.kif",
        "t3-02-sente.kif",
        "t3-03-sente.kif",
        "t3-04-gote.kif",
        "t3-05-gote.kif",
        "t3-06-gote.kif",
        "t3-07-sente.kif",
        "t3-08-gote.kif",
        "t3-09-sente.kif",
        "t3-10-gote.kif",
        "t3-11-sente.kif",
        "t3-12-sente.kif",
        "t3-13-sente.kif",
        "t3-14-gote.kif",
      ];
      expect(kifuNameProblems("/kifu", files)).toEqual([]);
    });

    it("tatsunami-long の実物の名前(10 件)は問題 0 件", () => {
      const files = [
        "tl-01-sente.kif",
        "tl-02-sente.kif",
        "tl-03-gote.kif",
        "tl-04-gote.kif",
        "tl-05-gote.kif",
        "tl-06-sente.kif",
        "tl-07-gote.kif",
        "tl-08-gote.kif",
        "tl-09-gote.kif",
        "tl-10-sente.kif",
      ];
      expect(kifuNameProblems("/kifu", files)).toEqual([]);
    });

    it("g01-sente.kif〜g20-gote.kif は通る", () => {
      const files: string[] = [];
      for (let i = 1; i <= 20; i += 1) {
        const n = String(i).padStart(2, "0");
        files.push(`g${n}-${i % 2 === 1 ? "sente" : "gote"}.kif`);
      }
      expect(kifuNameProblems("/kifu", files)).toEqual([]);
    });

    it("日付と対局 ID を含む名前は止まり、badNumber が 20260503 と 0 の 2 件になる(全部返る・打ち切らない)", () => {
      const files = ["01_x-sente.kif", "02_y-sente.kif", "03_20260503_a0kABJIn-sente.kif"];
      const problems = kifuNameProblems("/kifu", files);
      expect(problems).toEqual([
        { fileName: "03_20260503_a0kABJIn-sente.kif", kifuId: "03_20260503_a0kABJIn", gameNo: 3, badNumber: 20260503 },
        { fileName: "03_20260503_a0kABJIn-sente.kif", kifuId: "03_20260503_a0kABJIn", gameNo: 3, badNumber: 0 },
      ]);
    });

    it("1 つの名前に悪い数字が 3 つあれば全部(3 件)返る(最初の 1 つで打ち切らない)", () => {
      const files = ["99_2026_5000-sente.kif"];
      const problems = kifuNameProblems("/kifu", files);
      expect(problems.map((p) => p.badNumber)).toEqual([99, 2026, 5000]);
    });

    it("局番号が合っていない名前で止まる(gameNo は並び順から決まることを示す)", () => {
      // 1 件だけなので listGames の並び順で gameNo = 1 になる。id の「07」は 7 なので許されない。
      const problems = kifuNameProblems("/kifu", ["g07-sente.kif"]);
      expect(problems).toEqual([{ fileName: "g07-sente.kif", kifuId: "g07", gameNo: 1, badNumber: 7 }]);
    });

    it(".kif 等が 0 件なら空配列", () => {
      expect(kifuNameProblems("/kifu", ["readme.txt", "notes.md"])).toEqual([]);
    });

    it("数字を含まない名前は通る(この検査は数字しか見ない)", () => {
      expect(kifuNameProblems("/kifu", ["lishogi-abcdefgh-sente.kif"])).toEqual([]);
    });

    it("--me が無く -sente/-gote も無い名前は PipelineConfigError をそのまま出す(判定を作り直さない)", () => {
      expect(() => kifuNameProblems("/kifu", ["no-suffix.kif"])).toThrow(PipelineConfigError);
    });
  });
});

// REPLAN_BRIEF.md §3(C)。「既存の 44 局の納品の動きを変えていない」の根拠 ― 実際の材料の揃った work
// (本体ツリー。書き込みはしない・読むだけ)を読む probe で `planDeliver` を 17 回呼び、17 回すべてが
// 1 回目と `toStrictEqual` であることを見る(tsx の使い捨てではなく、この試験として置く)。
// **この材料(scripts/playtest/out/ は gitignore)を持たない環境では skip する**(このファイルを他の
// 開発環境・CI で壊さないため。実装担当の判断・報告に明記)。
describe("planDeliver は実際の work でも冪等(§3(C)。材料が無い環境では skip)", () => {
  const REPLAN_OUT_ROOT = "/Users/midoriko/Desktop/sgogi-coach/scripts/playtest/out";
  const REAL_WORK = `${REPLAN_OUT_ROOT}/tatsunami3/pipe`;
  const REAL_KIFU_DIR = `${REPLAN_OUT_ROOT}/tatsunami3/kifu`;
  const REAL_PATIENT = `${REAL_WORK}/report/patient_report_data.json`;
  const materialsReady = existsSync(REAL_WORK) && existsSync(REAL_KIFU_DIR) && existsSync(REAL_PATIENT);

  const realProbe: DeliverProbe = {
    exists: (p) => existsSync(p),
    hasJsonl: (d) => existsSync(d) && readdirSync(d).some((name) => name.endsWith(".jsonl")),
    fixedKifuFiles: (d) =>
      existsSync(d)
        ? readdirSync(d)
            .filter((name) => name.endsWith(".fixed.json"))
            .sort()
            .map((name) => `${d}/${name}`)
        : [],
    timeUpLossCount: (patientPath) => {
      if (!existsSync(patientPath)) return 0;
      try {
        const data = JSON.parse(readFileSync(patientPath, "utf-8")) as { time?: { timeUpLosses?: unknown[] | null } };
        const losses = data.time?.timeUpLosses;
        return Array.isArray(losses) ? losses.length : 0;
      } catch {
        return 0;
      }
    },
    mtimeMs: (p) => (existsSync(p) ? statSync(p).mtimeMs : undefined),
  };

  it.skipIf(!materialsReady)("実際の work(tatsunami3/pipe)で 17 回呼んでも 1 回目と一致する", () => {
    // 表示名等は patient_report_data.json から読む(報告に書く値ではないので、コードにも literal で書かない)。
    const patientData = JSON.parse(readFileSync(REAL_PATIENT, "utf-8")) as { person: string; title: string; today: string };
    const realArgs = parseDeliverArgs([
      "--person",
      "p2",
      "--kifu-dir",
      REAL_KIFU_DIR,
      "--work",
      REAL_WORK,
      "--time-limit-sec",
      "180",
      "--name",
      patientData.person,
      "--title",
      patientData.title,
      "--today",
      patientData.today,
      "--out",
      `${REPLAN_OUT_ROOT}/_replan/out_dry_ready`,
    ]);
    const first = planDeliver(realArgs, realProbe, (t) => t);
    // **段の数は一覧から取る**(足すたびに数を書き換えない ― 書き換え忘れが黙る)。
    expect(first).toHaveLength(DELIVER_STAGES.length);
    for (let i = 0; i < DELIVER_STAGES.length - 1; i += 1) {
      expect(planDeliver(realArgs, realProbe, (t) => t)).toStrictEqual(first);
    }
  });
});

// ==================== 顧客向け出口の 4 段(STEP CUSTOMER-EXIT) ====================

describe("顧客向け出口の 4 段", () => {
  const argv = [...BASE_ARGV];
  const args = parseDeliverArgs(argv);
  const out = deliverOutPaths(args.out);
  const groups = groupListOf(args);
  const thisGroup = groupPaths({ work: args.work, timeLimitSec: args.timeLimitSec }, args.person);
  const plan = materialPlanOf(args);

  it("段は既存 17 段の後に入り、最後が exit-send(既存の順は動かない。⑤ の門は exit-candidates の直前)", () => {
    const stages = [...DELIVER_STAGES];
    // **⑤ の門は `exit-candidates` の直前**(2026-10-01。正本 ⑤ の行)。
    expect(stages.slice(-8)).toEqual(["exit-select", "exit-candidates", "exit-fill", "exit-gate", "exit-render", "exit-check",
                                      "check-delivery", "exit-send"]);
    // **直前であることを隣で見る**(「どこかに在る」では位置が留まらない)。
    expect(stages[stages.indexOf("exit-candidates") - 1]).toBe("exit-select");
    // **`exit-draft` は `exit-select` の直前**(S-3。2026-10-06)。
    expect(stages[stages.indexOf("exit-select") - 1]).toBe("exit-draft");
    // **⑥ は候補の直後・門の直前**(正本 ⑥ の行。2026-10-05)。両隣で見る。
    expect(stages[stages.indexOf("exit-fill") - 1]).toBe("exit-candidates");
    expect(stages[stages.indexOf("exit-fill") + 1]).toBe("exit-gate");
    // **`exit-send` は最後**(C-1b。局数を `patient_report_data.json` から読めるのはここ) ―
    // 器の門と禁止語の検査を**通った後**でなければ、落ちた冊子の写しを渡す入れ物に入れてしまう。
    expect(stages[stages.length - 1]).toBe("exit-send");
    expect(stages.indexOf("exit-send")).toBeGreaterThan(stages.indexOf("check-delivery"));
    // **既存 17 段の並びが 1 つも動いていない**(仕様「既存 17 段は触らない。足すだけ」)。
    expect(stages.slice(0, 16)).toEqual([
      "pipeline-gate", "pipeline-data", "prose-gate", "pipeline-pdf", "deliverables-pdf",
      "appendix3-answers", "appendix3-final", "appendix3-pdf",
      "appendix4-cause", "appendix4-search", "appendix4-pdf",
      "answer-menu", "answer-draft", "answer-gate", "answer-check", "answer-pdf",
    ]);
    // 22 → 23(⑤ の門 `exit-select` を足した。2026-10-01)→ 24(⑥ `exit-fill`。2026-10-05)→ 25(`exit-draft`。S-3。2026-10-06)。
    expect(stages).toHaveLength(25);
  });

  // ---- S-3(2026-10-06。計画 CORE_CONNECTION_S3_PLAN §2.1 の (d))----
  describe("exit-draft(S-3)", () => {
    it("--seat-run が無ければ skip で、既存の顧客の流れは動かない", () => {
      const steps = planDeliver(argsOf(), fakeProbe({}), (t) => t);
      const step = steps.find((s) => s.stage === "exit-draft")!;
      expect(step.action).toBe("skip");
      expect(step.reason).toBe("--seat-run 無し");
      expect(step.args).toEqual([]);
      // 既存の `exit-select` 段は不変。
      expect(steps.find((s) => s.stage === "exit-select")!.action).toBe("gate");
    });

    it("--seat-run があれば run で、引数の並びが exitSelect.ts --draft の必須旗どおり", () => {
      const steps = planDeliver(argsOf(["--seat-run", "run20261006abc"]), fakeProbe({}), (t) => t);
      const step = steps.find((s) => s.stage === "exit-draft")!;
      expect(step.action).toBe("run");
      const customerDir = customerDirOf(argsOf().groups);
      const packetPaths = exitPacketPaths(customerDir);
      const selectPaths = exitSelectPaths(customerDir);
      expect(step.args).toEqual(exitDraftCommand(customerDir, "run20261006abc", "2026-09-24"));
      expect(step.args).toEqual([
        "--draft",
        "--packet", packetPaths.packet,
        "--integration", `${packetPaths.seatsDir}/run20261006abc/integration.json`,
        "--request", packetPaths.request,
        "--obs-registry", "docs/OBSERVATION_ITEMS.md",
        "--today", "2026-09-24",
        "--out", selectPaths.selectionDraft,
      ]);
    });
  });

  it("--from exit-gate で書き手の席から再開できる", () => {
    expect(stagesFrom("exit-gate")).toEqual(["exit-gate", "exit-render", "exit-check",
                                             "check-delivery", "exit-send"]);
    // ⑥ からの再開は門を飛ばさない。
    expect(stagesFrom("exit-fill")).toEqual(["exit-fill", "exit-gate", "exit-render", "exit-check",
                                             "check-delivery", "exit-send"]);
  });

  // ---- ⑥ 段 `exit-fill`(2026-10-05。計画 PLAN_EXIT_FILL §7 の F-9)----
  describe("exit-fill(⑥)", () => {
    const customerDir = customerDirOf(args.groups);
    const packetPaths = exitPacketPaths(customerDir);
    const selectPaths = exitSelectPaths(customerDir);

    it("packet が在れば走り、無ければ飛ぶ(書き手の道を消さない)", () => {
      const ready = planDeliver(args, fakeProbe({ files: [packetPaths.packet] }), (t) => t).find((s) => s.stage === "exit-fill")!;
      expect(ready.action).toBe("run");
      expect(ready.tool).toBe("exit-fill");
      const notReady = planDeliver(args, fakeProbe({}), (t) => t).find((s) => s.stage === "exit-fill")!;
      expect(notReady.action).toBe("skip");
      expect(notReady.reason).toContain("packet が無い");
      // 選択だけ在っても packet が無ければ飛ぶ(数を引く相手が無い)。
      const selOnly = planDeliver(args, fakeProbe({ files: [selectPaths.answerSelection] }), (t) => t).find((s) => s.stage === "exit-fill")!;
      expect(selOnly.action).toBe("skip");
    });

    it("引数は ⑤ の採用・packet・request・候補・本編・slot_map・周のフォルダ・言い換えの文 + 門と同じ材料の旗", () => {
      const cmd = exitFillCommand(groups, fakeProbe({}), out, plan, customerDir);
      const valueOf = (flag: string) => cmd[cmd.indexOf(flag) + 1];
      expect(valueOf("--selection")).toBe(selectPaths.answerSelection);
      expect(valueOf("--packet")).toBe(packetPaths.packet);
      expect(valueOf("--request")).toBe(packetPaths.request);
      expect(valueOf("--candidates")).toBe(out.exitCandidates);
      expect(valueOf("--md")).toBe(out.honbunMd);
      expect(valueOf("--out-slot-map")).toBe(out.slotMap);
      expect(valueOf("--seats-dir")).toBe(packetPaths.seatsDir);
      expect(valueOf("--texts")).toBe(selectPaths.fillTexts);
      // **門と同じ材料の旗**(埋めた本編を書く前に check_answer を通すため)。
      const material = answerMaterialFlags(groups, fakeProbe({}), out, plan);
      expect(cmd.slice(cmd.length - material.length)).toEqual(material);
      // 名前は渡さない(本編は見本用にも載る)。
      expect(cmd).not.toContain(args.name);
    });

    it("見出しの指し手の字の材料は REPORT_DATA_DIR(付録 3・本編と同じ・組の順)", () => {
      const step = planDeliver(args, fakeProbe({ files: [packetPaths.packet] }), (t) => t).find((s) => s.stage === "exit-fill")!;
      const appendix3 = planDeliver(args, fakeProbe({ files: [packetPaths.packet] }), (t) => t).find((s) => s.stage === "appendix3-pdf")!;
      expect(step.env).toEqual({ REPORT_DATA_DIR: groups.map((g) => g.reportDir).join(",") });
      expect(step.env).toEqual(appendix3.env);
    });

    it("置き場は顧客のフォルダの packet/・llm-seats/・exit/(work の外。組み直しても消えない)", () => {
      expect(packetPaths.packet).toBe(path.join(customerDir, "packet", "observation-packet.json"));
      expect(packetPaths.request).toBe(path.join(customerDir, "packet", "observation-request.json"));
      expect(packetPaths.seatsDir).toBe(path.join(customerDir, "llm-seats"));
      expect(selectPaths.fillTexts).toBe(path.join(customerDir, "exit", "fill_texts.json"));
      expect(out.slotMap).toBe(path.join(args.out, "direct", "slot_map.json"));
      // `--out` の安全装置は slot_map.json を知っている(知らないと納品が止まる)。
      expect(unexpectedOutFiles([], ["slot_map.json"])).toEqual([]);
    });

    it("門には ⑤・① の成果物のうち在るものだけを渡す(無いものは渡さない)", () => {
      const none = exitGateCommand(groups, fakeProbe({}), out, plan, customerDir);
      expect(none).not.toContain("--packet");
      expect(none).not.toContain("--request");
      expect(none).not.toContain("--answer-selection");
      const all = exitGateCommand(groups, fakeProbe({ files: [packetPaths.packet, packetPaths.request, selectPaths.answerSelection] }), out, plan, customerDir);
      expect(all[all.indexOf("--packet") + 1]).toBe(packetPaths.packet);
      expect(all[all.indexOf("--request") + 1]).toBe(packetPaths.request);
      expect(all[all.indexOf("--answer-selection") + 1]).toBe(selectPaths.answerSelection);
      // 1 つだけ在る形でも、その 1 つだけ。
      const one = exitGateCommand(groups, fakeProbe({ files: [packetPaths.request] }), out, plan, customerDir);
      expect(one).toContain("--request");
      expect(one).not.toContain("--packet");
      // 顧客のフォルダを渡さない呼び方(既存)は旗が増えない。
      expect(exitGateCommand(groups, fakeProbe({ files: [packetPaths.packet] }), out, plan)).not.toContain("--packet");
      // 器の門も `--request` を在るときだけ。
      const cs = checkStructureCommand(groups, fakeProbe({ files: [packetPaths.request] }), out, plan, thisGroup, args.out, customerDir);
      expect(cs[cs.indexOf("--request") + 1]).toBe(packetPaths.request);
      expect(checkStructureCommand(groups, fakeProbe({}), out, plan, thisGroup, args.out, customerDir)).not.toContain("--request");
    });

    it("計画の中で ⑥ の段は門の直前に並び、門の引数に packet が入る", () => {
      const steps = planDeliver(args, fakeProbe({ files: [packetPaths.packet] }), (t) => t);
      const names = steps.map((s) => s.stage);
      expect(names[names.indexOf("exit-fill") + 1]).toBe("exit-gate");
      const gate = steps.find((s) => s.stage === "exit-gate")!;
      expect(gate.args[gate.args.indexOf("--packet") + 1]).toBe(packetPaths.packet);
    });
  });

  it("索引の名前は PDF の名前から導く(手で書かない)", () => {
    expect(pageIndexNameOf("9_本編_本人用.pdf")).toBe("9_本編_本人用_page_index.json");
    // `exit_body.py` と `exit_index.PageIndexRecorder.path_for` が使う形。**形が変わったらここで気づく。**
    expect(out.honbunIndex.endsWith("/9_本編_本人用_page_index.json")).toBe(true);
    expect(out.appendix3Index.endsWith("/5_付録3_直接の答え_page_index.json")).toBe(true);
    expect(() => pageIndexNameOf("表紙.md")).toThrow(DeliverArgError);
  });

  it("--out の安全装置が、道具が書く索引 2 本を知らないファイルとして止めない", () => {
    // これを忘れると、**2 回目の納品が「知らないファイルがある」で何もせず止まる**。
    const names = [
      "9_本編.md", "9_本編_本人用.pdf", "9_本編_見本用.pdf", "9_本編_本人用_page_index.json",
      "10_付録_表紙.md", "10_付録_表紙.pdf", "10_付録_数の出どころ.pdf", "10_付録_page_index.json",
      "5_付録3_直接の答え_page_index.json",
    ];
    expect(unexpectedOutFiles(names, ["exit_candidates.json"])).toEqual([]);
    expect(unexpectedOutFiles(["知らない.pdf"], [])).toEqual(["知らない.pdf"]);
  });

  it("候補の段は本編の md と候補の JSON を出し、材料の旗は B と同じ並び", () => {
    const cmd = exitCandidatesCommand(groups, fakeProbe({}), out, plan, thisGroup, "2026-09-29", "3 分切れ負け");
    // **固定棋譜のフォルダ**(生の `--kifu-dir` ではない)。取り違えると工程の最後で落ちる。
    expect(cmd.slice(0, 6)).toEqual(["--out-md", out.honbunMd, "--out-json", out.exitCandidates, "--kifu-dir", thisGroup.fixedKifuDir]);
    expect(thisGroup.fixedKifuDir).not.toBe(args.kifuDir);
    // **冒頭の 1 文目に入る日付と組の名**(P-162・仕様 §4d)。
    expect(cmd.slice(6, 10)).toEqual(["--today", "2026-09-29", "--group-label", "3 分切れ負け"]);
    // **2 つ目の材料の並びを作らない**(片方だけ直ると数が食い違う)。
    expect(cmd.slice(10)).toEqual(answerMaterialFlags(groups, fakeProbe({}), out, plan));
  });

  it("組の名は 1 か所から来る ― 渡さなければ「N 分」のまま(仕様 §4d)", () => {
    // **渡さなければ出力不変**。これが崩れると、2 回目の納品で付録の見出しが黙って変わる。
    expect(groupLabelOf({ timeLimitSec: 180 })).toBe(groupLabelOfTimeLimitSec(180));
    expect(groupLabelOf({ timeLimitSec: 180, groupLabel: undefined })).toBe(groupLabelOfTimeLimitSec(180));
    // **人間が渡したラベルが勝つ。**
    expect(groupLabelOf({ timeLimitSec: 180, groupLabel: "3 分切れ負け" })).toBe("3 分切れ負け");
  });

  it("本編の冒頭と付録の見出しは、同じ 1 つのラベルを受け取る(名前が食い違わない)", () => {
    // 仕様 §4d の門。**2 か所が別の関数からラベルを引くと、本編が「3 分切れ負け」・付録が「3 分」になる。**
    const label = groupLabelOf({ timeLimitSec: 180, groupLabel: "3 分切れ負け" });
    const honbun = exitCandidatesCommand(groups, fakeProbe({}), out, plan, thisGroup, "2026-09-29", label);
    const cover = exitCoverCommand(thisGroup, out, label);
    const labelOf = (cmd: readonly string[], flag: string) => cmd[cmd.indexOf(flag) + 1];
    expect(labelOf(honbun, "--group-label")).toBe(labelOf(cover, "--group"));
    expect(labelOf(honbun, "--group-label")).toBe("3 分切れ負け");
  });

  it("書き手の席の検査は、本編の md と候補の JSON を突き合わせる", () => {
    const cmd = exitGateCommand(groups, fakeProbe({}), out, plan);
    expect(cmd[0]).toBe(out.honbunMd);
    expect(cmd.slice(1, 3)).toEqual(["--candidates", out.exitCandidates]);
  });

  it("索引は、それが書かれた PDF と対にする(複製と組ませない)", () => {
    const pairs = exitSourceIndexPairs(thisGroup, out);
    expect(pairs).toEqual([
      [`${thisGroup.reportDir}/main_page_index.json`, thisGroup.mainPdf],
      [out.appendix3Index, out.appendix3],
    ]);
    // **付録 1 は work の中で対になっている**(納品フォルダの複製 `out.main` とは組ませない) ―
    // 複製だけ作り直したときに古い索引が通るのを防ぐ。
    expect(pairs[0]![1]).not.toBe(out.main);
  });

  it("表紙は md と PDF を同じ実行で作る(2 つの版が並ばない)", () => {
    const cmd = exitCoverCommand(thisGroup, out, "3 分");
    expect(cmd).toContain("--out-pdf");
    expect(cmd[cmd.indexOf("--out") + 1]).toBe(out.exitCoverMd);
    expect(cmd[cmd.indexOf("--out-pdf") + 1]).toBe(out.exitCoverPdf);
    expect(cmd[cmd.indexOf("--group") + 1]).toBe("3 分");
  });

  it("束ねは表紙 PDF を**ページ番号なしで**渡し(全ページ)、索引と PDF の対を渡す", () => {
    const cmd = exitRenderCommand(thisGroup, out);
    const cover = cmd[cmd.indexOf("--cover") + 1];
    expect(cover).toBe(out.exitCoverPdf);
    // **`:<ページ>` を付けないこと**(器の単独束 C-4)。表紙 PDF は表紙 1 ページのあとに
    // 「付録へ回した節」(分母の表)を載せるので、`:1` と書くと 2 ページ目が束から落ち、
    // 顧客が読む表がどこにも出なくなる。
    expect(cover).not.toMatch(/:\d+$/);
    const sources = cmd.filter((_v, i) => cmd[i - 1] === "--source-index");
    expect(sources).toEqual(exitSourceIndexPairs(thisGroup, out).map(([i, p]) => `${i}:${p}`));
    expect(cmd[cmd.indexOf("--out-index") + 1]).toBe(out.exitIndex);
  });

  it("本編の組版は本人用・見本用を渡す。**名前は渡さない**(P-170)", () => {
    const cmd = exitBodyCommand(groups, fakeProbe({}), out, plan);
    expect(cmd[0]).toBe(out.honbunMd);
    expect(cmd[cmd.indexOf("--out-person") + 1]).toBe(out.honbunPerson);
    expect(cmd[cmd.indexOf("--out-sample") + 1]).toBe(out.honbunSample);
    // **`--person` が無いこと**。在れば `exit_body.py` の既定「本人」が上書きされ、
    // 盤の名札に渡した語が入る(実名を渡すと見本用にも乗る)。
    expect(cmd).not.toContain("--person");
  });

  it("本編の組版の引数に、顧客の名前になりうる語が 1 つも無い(P-170)", () => {
    const cmd = exitBodyCommand(groups, fakeProbe({}), out, plan);
    // **args.name・args.title を渡す道を塞ぐ**。関数の引数に名前が無いので、
    // 呼ぶ側が名前を混ぜるには引数を足すしかない(足したらこの試験が落ちる)。
    expect(exitBodyCommand.length).toBe(4);
    expect(cmd).not.toContain(args.name);
    expect(cmd).not.toContain(args.title);
  });

  it("器の門は本編の索引も渡す(検査 4 が対応表のページ数を索引から取るため)", () => {
    const cmd = checkStructureCommand(groups, fakeProbe({}), out, plan, thisGroup, args.out);
    expect(cmd[0]).toBe(args.out);
    expect(cmd[cmd.indexOf("--honbun-index") + 1]).toBe(out.honbunIndex);
    expect(cmd[cmd.indexOf("--page-index") + 1]).toBe(out.exitIndex);
    // 組版が書いた索引も渡す(束ねた値が書き換えられていないかを門が見る)。
    const sources = cmd.filter((_v, i) => cmd[i - 1] === "--source-index");
    expect(sources).toEqual(exitSourceIndexPairs(thisGroup, out).map(([i]) => i));
  });

  it("候補の段は下書きがあれば飛ばす(書き手の編集を上書きしない)", () => {
    const withDraft = fakeProbe({ files: [out.honbunMd, out.exitCandidates] });
    const step = planDeliver(args, withDraft, (t) => t).find((s) => s.stage === "exit-candidates")!;
    expect(step.action).toBe("skip");
    const without = planDeliver(args, fakeProbe({}), (t) => t).find((s) => s.stage === "exit-candidates")!;
    expect(without.action).toBe("run");
  });

  it("候補の JSON が無くても、md が在れば段は走らない(書き手の md を消さない)", () => {
    // **実際に書き手の 92 行を消した**(2026-09-29)。判定が `md と JSON の両方が在る` だったため、
    // **JSON を消しただけで段が走り、md が素の下書きに戻った**(git の追跡外で戻せなかった)。
    // JSON が無いまま進めば段 `exit-gate` が「候補の JSON に p1Numbers が無い」で止まる ―
    // **止まるのは良く、消すのは悪い。**
    const mdOnly = fakeProbe({ files: [out.honbunMd] });
    expect(planDeliver(args, mdOnly, (t) => t).find((s) => s.stage === "exit-candidates")!.action).toBe("skip");
    const jsonOnly = fakeProbe({ files: [out.exitCandidates] });
    expect(planDeliver(args, jsonOnly, (t) => t).find((s) => s.stage === "exit-candidates")!.action).toBe("run");
  });

  it("書き手の席は道具つきの確認点(fs を見るだけの gate ではない)", () => {
    const step = planDeliver(args, fakeProbe({}), (t) => t).find((s) => s.stage === "exit-gate")!;
    expect(step.action).toBe("gate");
    // **`tool` が `"gate"` ではない**ことが、呼び出し側が python を回す合図になっている。
    expect(step.tool).toBe("exit-gate");
    const proseStep = planDeliver(args, fakeProbe({}), (t) => t).find((s) => s.stage === "prose-gate")!;
    expect(proseStep.tool).toBe("gate");
  });

  it("本編の組版は、本人用が md より新しいときだけ飛ばす", () => {
    const stale = fakeProbe({ mtimes: { [out.honbunMd]: 200, [out.honbunPerson]: 100, [out.honbunSample]: 100 } });
    expect(planDeliver(args, stale, (t) => t).find((s) => s.stage === "exit-render")!.action).toBe("run");
    const fresh = fakeProbe({ mtimes: { [out.honbunMd]: 100, [out.honbunPerson]: 200, [out.honbunSample]: 200 } });
    expect(planDeliver(args, fresh, (t) => t).find((s) => s.stage === "exit-render")!.action).toBe("skip");
    // 見本用だけ古い場合も作り直す(片方だけ古い版が顧客に渡るのを防ぐ)。
    const halfStale = fakeProbe({ mtimes: { [out.honbunMd]: 100, [out.honbunPerson]: 200, [out.honbunSample]: 50 } });
    expect(planDeliver(args, halfStale, (t) => t).find((s) => s.stage === "exit-render")!.action).toBe("run");
  });
});

describe("人の席の時間(原価③。仕様 §5)", () => {
  const blocked = (stage: string, at: string) =>
    JSON.stringify({ stage, startedAt: at, finishedAt: at, rc: 1, humanGate: true });

  it("止まった時刻から通った時刻までの差を秒で返す", () => {
    const lines = [blocked("exit-gate", "2026-09-29T01:00:00.000Z")];
    expect(seatSecondsOf(lines, "exit-gate", "2026-09-29T01:30:00.000Z")).toBe(1800);
  });

  it("止まった記録が無ければ測らない(0 と書かない)", () => {
    expect(seatSecondsOf([], "exit-gate", "2026-09-29T01:00:00.000Z")).toBeUndefined();
    // 他の段で止まった記録は使わない(段ごとに分けて測るため)。
    const other = [blocked("prose-gate", "2026-09-29T01:00:00.000Z")];
    expect(seatSecondsOf(other, "exit-gate", "2026-09-29T01:30:00.000Z")).toBeUndefined();
  });

  it("同じ段で何度も止まったら、最後に止まった時刻から測る", () => {
    const lines = [blocked("exit-gate", "2026-09-29T01:00:00.000Z"), blocked("exit-gate", "2026-09-29T02:00:00.000Z")];
    expect(seatSecondsOf(lines, "exit-gate", "2026-09-29T02:00:10.000Z")).toBe(10);
  });

  it("一度通した後の再実行では測らない(同じ待ち時間を二度書かない)", () => {
    // 実測で踏んだ(2026-09-29): 止まった記録を全部たどって最後のものを採る作りだと、
    // **通した後の再実行が同じ席を「13 秒」と書き直した**(本当は 1 秒だった)。
    const passed = JSON.stringify({ stage: "exit-gate", startedAt: "x", finishedAt: "2026-09-29T01:10:00.000Z", rc: "skip", humanGate: false, seatSeconds: 600 });
    const lines = [blocked("exit-gate", "2026-09-29T01:00:00.000Z"), passed];
    expect(seatSecondsOf(lines, "exit-gate", "2026-09-29T02:00:00.000Z")).toBeUndefined();
  });

  it("読めない行・通った記録・負の差は測らない", () => {
    const passed = JSON.stringify({ stage: "exit-gate", startedAt: "x", finishedAt: "2026-09-29T01:00:00.000Z", rc: 0, humanGate: false });
    expect(seatSecondsOf([passed], "exit-gate", "2026-09-29T02:00:00.000Z")).toBeUndefined();
    const broken = ["{壊れた", "", blocked("exit-gate", "2026-09-29T01:00:00.000Z")];
    expect(seatSecondsOf(broken, "exit-gate", "2026-09-29T01:00:30.000Z")).toBe(30);
    // 手で編集された記録で**負の席時間**という有り得ない数を残さない。
    const future = [blocked("exit-gate", "2026-09-29T03:00:00.000Z")];
    expect(seatSecondsOf(future, "exit-gate", "2026-09-29T01:00:00.000Z")).toBeUndefined();
  });

  it("記録の行に seatSeconds を足せる(既存の 5 つの鍵は変わらない)", () => {
    const line = deliverLogLineOf({ stage: "exit-gate", startedAt: "a", finishedAt: "b", rc: 0, humanGate: false, seatSeconds: 42 });
    expect(JSON.parse(line)).toEqual({ stage: "exit-gate", startedAt: "a", finishedAt: "b", rc: 0, humanGate: false, seatSeconds: 42 });
    // 渡さなければ鍵自体が付かない(**測っていないものを数にしない**)。
    const plain = deliverLogLineOf({ stage: "exit-gate", startedAt: "a", finishedAt: "b", rc: 0, humanGate: false });
    expect(Object.keys(JSON.parse(plain) as object)).toEqual(["stage", "startedAt", "finishedAt", "rc", "humanGate"]);
  });
});

describe("送付用の名前(器の単独束 C-1)", () => {
  it("顧客に届く 2 冊の名前(局数と組の名が入る)", () => {
    expect(deliverSendNames(25, "3 分")).toEqual({
      honbun: "01_本編_対局後診断_3分25局.pdf",
      appendix: "02_付録_数の出どころ_3分25局.pdf",
    });
    // **継続の顧客で同じ名前にならない**(局数と組の名の両方が効く)
    expect(deliverSendNames(25, "10 分").honbun).toBe("01_本編_対局後診断_10分25局.pdf");
    expect(deliverSendNames(20, "3 分").honbun).toBe("01_本編_対局後診断_3分20局.pdf");
    expect(deliverSendNames(25, "3 分").honbun).not.toBe(deliverSendNames(25, "10 分").honbun);
  });

  it("空白は名前から外す(人間が渡すラベルは空白を含む)", () => {
    const names = deliverSendNames(25, "3 分切れ負け");
    expect(names.honbun).toBe("01_本編_対局後診断_3分切れ負け25局.pdf");
    // **どちらの名前にも空白が残っていない**(全角の空白も外れる)
    for (const name of [names.honbun, names.appendix]) expect(name).not.toMatch(/\s/);
    expect(deliverSendNames(25, "3　分").honbun).toBe("01_本編_対局後診断_3分25局.pdf");
  });

  it("素の並べ替えで先頭が本編(名前だけで最初に読むものが分かる)", () => {
    // **人間の要求を機械で固定する** ― `ls` で並べると付録が本編の上に来ていたため、
    // 5 人目の本人が「まず順番に上の付録から選びました」と書いた(実測された取り違え)
    const names = deliverSendNames(25, "3 分");
    expect([names.appendix, names.honbun].sort()[0]).toBe(names.honbun);
    expect([names.honbun, names.appendix].sort()[0]).toBe(names.honbun);
  });

  it("黙って変な名前を作らない(局数とラベルを検める)", () => {
    for (const games of [0, -1, 2.5, Number.NaN]) {
      expect(() => deliverSendNames(games, "3 分"), `局数 ${games}`).toThrow(DeliverArgError);
    }
    expect(() => deliverSendNames(25, "   ")).toThrow(DeliverArgError);
    expect(() => deliverSendNames(25, "")).toThrow(DeliverArgError);
  });

  it("2 段の名前は 1 か所(封の照合は原本の側)", () => {
    expect(DELIVER_SEND_DIRS).toEqual({ original: "原本", send: "送付" });
  });
});

describe("送付用の段(器の単独束 C-1b)", () => {
  const OUT = "/tmp/にせもの/deliver1";
  const out = deliverOutPaths(OUT);
  const send = deliverSendPaths(OUT);

  /** 見えているものの合成。**在るファイルと、中身が同じ組**を並べで渡す。 */
  function probeOf(exist: readonly string[], same: readonly string[][] = [], pdfs: readonly string[] = []) {
    const has = new Set(exist);
    const pairs = new Set(same.map(([a, b]) => `${a} -> ${b}`));
    return {
      exists: (p: string) => has.has(p),
      sameBytes: (a: string, b: string) => pairs.has(`${a} -> ${b}`),
      pdfNamesIn: (d: string) => (d === send.sendDir ? [...pdfs] : []),
    };
  }

  it("送付用は納品フォルダの隣・2 段", () => {
    expect(send.dir).toBe("/tmp/にせもの/deliver1_送付用");
    expect(send.originalDir).toBe(`/tmp/にせもの/deliver1_送付用/${DELIVER_SEND_DIRS.original}`);
    expect(send.sendDir).toBe(`/tmp/にせもの/deliver1_送付用/${DELIVER_SEND_DIRS.send}`);
    // **末尾の / を足しても同じ場所**(`deliver1/_送付用` のような入れ子を作らない)。
    expect(deliverSendPaths(`${OUT}/`).dir).toBe(send.dir);
  });

  it("原本に 4 冊(名前はそのまま)・送付に 2 冊(改名)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    // **6 組**(原本 4 + 送付 2)。数がそろっていないので、片方だけ数える取り違えが黙らない。
    expect(pairs).toHaveLength(6);
    expect(DELIVER_ORIGINAL_KEYS).toHaveLength(4);
    const originals = pairs.filter(([, dst]) => dst.startsWith(send.originalDir));
    expect(originals.map(([, dst]) => dst.slice(send.originalDir.length + 1))).toEqual([
      "9_本編_本人用.pdf", "9_本編_見本用.pdf", "10_付録_表紙.pdf", "10_付録_数の出どころ.pdf",
    ]);
    const sent = pairs.filter(([, dst]) => dst.startsWith(send.sendDir));
    expect(sent).toEqual([
      [out.honbunPerson, `${send.sendDir}/01_本編_対局後診断_3分25局.pdf`],
      [out.exitAppendix, `${send.sendDir}/02_付録_数の出どころ_3分25局.pdf`],
    ]);
    // **見本用は渡さない**(他人に見せるもので、顧客に渡すものではない)。
    expect(sent.some(([src]) => src === out.honbunSample)).toBe(false);
    // **写す元は納品フォルダのまま**(動かさないので、元の場所が行き先になっていない)。
    for (const [src, dst] of pairs) expect(src).not.toBe(dst);
  });

  it("行き先が無ければ写す", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const d = sendCopyDecisions(pairs, send.sendDir, probeOf(pairs.map(([src]) => src)));
    expect(d.problems).toEqual([]);
    expect(d.copy).toHaveLength(6);
    expect(d.skip).toEqual([]);
  });

  it("同じ中身が在れば写さない(冪等)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const probe = probeOf(pairs.flat(), pairs,
                          ["01_本編_対局後診断_3分25局.pdf", "02_付録_数の出どころ_3分25局.pdf"]);
    const d = sendCopyDecisions(pairs, send.sendDir, probe);
    expect(d.problems).toEqual([]);
    expect(d.copy).toEqual([]);
    expect(d.skip).toHaveLength(6);
  });

  it("**行き先が在って中身が違えば止まる**(黙って上書きしない)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    // 在るのは全部。**中身が同じなのは 1 組目だけ** ― 残り 5 組は「違う」。
    const probe = probeOf(pairs.flat(), [pairs[0]!]);
    const d = sendCopyDecisions(pairs, send.sendDir, probe);
    expect(d.copy).toEqual([]);
    expect(d.skip).toEqual([pairs[0]![1]]);
    expect(d.problems).toHaveLength(5);
    expect(d.problems[0]).toContain("上書きしない");
  });

  it("写す元が無ければ止まる(空の入れ物を作らない)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const d = sendCopyDecisions(pairs, send.sendDir, probeOf([out.honbunPerson]));
    // 本人用は 2 か所へ写すので、残り 4 冊ぶんが「元が無い」。
    expect(d.problems).toHaveLength(4);
    for (const problem of d.problems) expect(problem).toContain("写す元が無い");
    expect(d.copy).toHaveLength(2);
  });

  it("**送付フォルダに予定外の PDF が在れば止まる**(既に渡した冊子を上に積まない)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const probe = probeOf(pairs.map(([src]) => src), [], ["対局後診断_25局_本編.pdf"]);
    const d = sendCopyDecisions(pairs, send.sendDir, probe);
    expect(d.problems).toHaveLength(1);
    expect(d.problems[0]).toContain("予定外の PDF");
    expect(d.problems[0]).toContain("対局後診断_25局_本編.pdf");
  });

  it("予定の 2 冊そのものは予定外ではない(自分の名前で止まらない)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const probe = probeOf(pairs.map(([src]) => src), [],
                          ["01_本編_対局後診断_3分25局.pdf", "02_付録_数の出どころ_3分25局.pdf"]);
    expect(sendCopyDecisions(pairs, send.sendDir, probe).problems).toEqual([]);
  });

  it("原本の名前は送付フォルダでは予定外(見る場所は送付フォルダだけ)", () => {
    // `原本/` には 4 冊入るが、**送付フォルダにその名前が在れば**止める ―
    // 顧客に渡す入れ物に納品の名前の冊子が在るのは、渡す前の形ではない。
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const probe = probeOf(pairs.map(([src]) => src), [], ["9_本編_本人用.pdf"]);
    const d = sendCopyDecisions(pairs, send.sendDir, probe);
    expect(d.problems).toHaveLength(1);
    expect(d.problems[0]).toContain("9_本編_本人用.pdf");
  });

  it("**局数は今回の組から読む(一覧の最後ではない)**", () => {
    // `--group-work` は**持ち時間の昇順**に並べる(README)。今回の組(`--work` = /w/now)を
    // **先頭**に、別の組を後ろに置く ― 独立監査がこの並びで「別の組の局数がファイル名に入る」
    // 欠陥を実物の手順で再現した(25 局の冊子に `…3分999局.pdf` が付き、rc=0 で静かに通った)。
    const args = argsOf(["--group-work", "/w/now", "--group-time-limit-sec", "180",
                         "--group-work", "/w/other", "--group-time-limit-sec", "600"]);
    const groups = groupListOf(args);
    // **今回の組が一覧の最後ではない**ことを土台で固定する(ここがそろうと欠陥が再現しない)。
    expect(groups).toHaveLength(2);
    expect(groups[groups.length - 1]!.work).toBe("/w/other");
    expect(exitSendPatientPath(args)).toBe(groups[0]!.patient);
    expect(exitSendPatientPath(args)).not.toBe(groups[groups.length - 1]!.patient);
    expect(exitSendPatientPath(args)).toContain("/w/now/");
    expect(exitSendPatientPath(args)).not.toContain("/w/other");
  });

  it("**並びが変わっても今回の組を指す(先頭でも末尾でもない)**", () => {
    // **1 つ目の材料は今回の組が先頭**なので、「先頭から読む」という誤りでは**同じ答えになり黙る**
    // (変異 W2 が実測で緑だった)。ここは**今回の組を真ん中に置いた 3 組**で測る ―
    // 先頭でも末尾でもない位置を通すと、並びに頼る書き方はどれも落ちる。
    const args = argsOf(["--group-work", "/w/slow", "--group-time-limit-sec", "60",
                         "--group-work", "/w/now", "--group-time-limit-sec", "180",
                         "--group-work", "/w/other", "--group-time-limit-sec", "600"]);
    const groups = groupListOf(args);
    expect(groups).toHaveLength(3);
    expect(groups[0]!.work).toBe("/w/slow");
    expect(groups[2]!.work).toBe("/w/other");
    expect(exitSendPatientPath(args)).toBe(groups[1]!.patient);
    expect(exitSendPatientPath(args)).not.toBe(groups[0]!.patient);
    expect(exitSendPatientPath(args)).not.toBe(groups[2]!.patient);
  });

  it("組が 1 つのときも同じ場所を指す", () => {
    const args = argsOf();
    expect(exitSendPatientPath(args)).toBe(groupListOf(args)[0]!.patient);
    expect(exitSendPatientPath(args).endsWith("/report/patient_report_data.json")).toBe(true);
  });

  it("**段は封の JSON を写さない・消さない**(司令塔の条件。2026-10-01)", () => {
    const pairs = exitSendPairs(out, send, 25, "3 分");
    // **書く先は 6 つだけ。**封(`封_exit_seal.json`)はこの一覧に無い ―
    // 封は**この段の後に人が `原本/` へ掛ける**もので、段が触ってよいものではない。
    // 毎回自動で掛け直すと封の意味が消える(段は 4 冊を書き、**何も消さない**)。
    expect(pairs.map(([, dst]) => dst.slice(dst.lastIndexOf("/") + 1))).toEqual([
      "9_本編_本人用.pdf", "9_本編_見本用.pdf", "10_付録_表紙.pdf", "10_付録_数の出どころ.pdf",
      "01_本編_対局後診断_3分25局.pdf", "02_付録_数の出どころ_3分25局.pdf",
    ]);
    // **封という語が行き先にも写す元にも出ない。**(名前が変わっても語で捕まえる)
    for (const [src, dst] of pairs) {
      expect(src).not.toContain("封");
      expect(dst).not.toContain("封");
      expect(dst.endsWith(".pdf")).toBe(true);
    }
  });

  it("封が既に在っても段は止まらない(PDF しか見ない)", () => {
    // `原本/` に封が在る状態で 2 回目を流しても、段は封を読まない・写さない。
    // `送付/` の一覧も **PDF だけ**を見るので、封が在っても「予定外」にはならない。
    const pairs = exitSendPairs(out, send, 25, "3 分");
    const probe = {
      exists: (p: string) => pairs.some(([src]) => src === p),
      sameBytes: () => false,
      // **封を混ぜて渡す。**`pdfNamesIn` の約束は「`*.pdf` の基底名」なので、
      // 封はここに出ない ― 出るようになったら(= 約束が変わったら)この試験が落ちる。
      pdfNamesIn: (_d: string) => [],
    };
    expect(sendCopyDecisions(pairs, send.sendDir, probe).problems).toEqual([]);
  });

  it("局数が 0 以下・組の名が空なら名前を作らない", () => {
    expect(() => exitSendPairs(out, send, 0, "3 分")).toThrow(DeliverArgError);
    expect(() => exitSendPairs(out, send, 25, "  ")).toThrow(DeliverArgError);
  });
});
