// STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 3)。lib/deliver.ts(純粋な部分)の試験。
// 流儀は lib/pipeline.test.ts と同じ(偽の fs / probe を注入し、引数の並びと済みの判定だけを見る)。
// **将棋の判断・数の集計はここにも無い**(引数の組み立てと段の順だけ)。

import { existsSync, readdirSync, readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import {
  DELIVER_STAGES,
  DeliverArgError,
  KIFU_NAME_FIXED_ALLOWED_NUMBERS,
  TODO_MARK,
  answerFactsCommand,
  answerMaterialFlags,
  checkAnswerCommand,
  checkDeliveryCommand,
  deliverLogLineOf,
  deliverOutPaths,
  directAnswersCommand,
  finalPositionsCommand,
  finalPositionsPartPath,
  groupListOf,
  groupPaths,
  groupsWithRead,
  kifuNameProblems,
  materialPlanOf,
  materialsPending,
  mergeFinalPositions,
  parseDeliverArgs,
  pipelineCommand,
  pipelineGateCommand,
  planDeliver,
  renderAnswerCommand,
  renderTimeCauseCommand,
  reportDataDirEnv,
  stagesFrom,
  timeCauseCommand,
  timeSearchCommand,
  unexpectedOutFiles,
  type DeliverArgs,
  type DeliverProbe,
} from "./deliver.js";
import { PipelineConfigError } from "./pipeline.js";

// ---- 偽の probe(見えているものを表で与える) ----

interface FakeWorld {
  files?: string[];
  jsonlDirs?: string[];
  fixed?: Record<string, string[]>;
  losses?: Record<string, number>;
}

function fakeProbe(world: FakeWorld): DeliverProbe {
  return {
    exists: (p) => (world.files ?? []).includes(p),
    hasJsonl: (d) => (world.jsonlDirs ?? []).includes(d),
    fixedKifuFiles: (d) => world.fixed?.[d] ?? [],
    timeUpLossCount: (p) => world.losses?.[p] ?? 0,
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
      "--name",
      "お客さま",
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

  it("旗の並びと回数が run_check.sh と同じ(patient×3・prose×1・whatif-data×2・whatif-v2-dir×2・read-dir×2・type-summary×2・whatif-pdf×3・direct×2・time-cause・time-search・menu)", () => {
    const counts = (flag: string): number => flags.filter((t) => t === flag).length;
    expect(counts("--patient")).toBe(3);
    expect(counts("--time-limit-sec")).toBe(3);
    expect(counts("--prose")).toBe(1);
    expect(counts("--whatif-data")).toBe(2);
    expect(counts("--whatif-v2-dir")).toBe(2);
    expect(counts("--read-dir")).toBe(2);
    expect(counts("--type-summary")).toBe(2);
    expect(counts("--whatif-pdf")).toBe(3);
    expect(counts("--direct")).toBe(2);
    expect(counts("--time-cause")).toBe(1);
    expect(counts("--time-search")).toBe(1);
    expect(counts("--menu")).toBe(1);
  });

  it("prose は今回の組(--work)の 1 本だけ、patient と同じフォルダ(<work>/report/prose.json)を渡す(局番号は組ごとに 1 から振られ、納品される付録 1 は今回の組の本編だけのため)", () => {
    const proses = flags.map((t, i) => (flags[i - 1] === "--prose" ? t : null)).filter((t): t is string => t !== null);
    expect(proses).toEqual(["/w/now/report/prose.json"]);
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

describe("stagesFrom", () => {
  it("--from が無ければ全段、あればその段から", () => {
    expect(stagesFrom(undefined)).toEqual([...DELIVER_STAGES]);
    expect(stagesFrom("answer-check")).toEqual(["answer-check", "answer-pdf", "check-delivery"]);
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

  it("計画の順どおり 17 段(段 pipeline-gate が先頭)", () => {
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
    expect(resumed.map((s) => s.stage)).toEqual(["answer-check", "answer-pdf", "check-delivery"]);
  });

  it("出力が既にあれば skip(済みの判定)", () => {
    const done = fakeProbe({
      files: [
        "/w/now/report/prose.json",
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
    expect(first).toHaveLength(17);
    for (let i = 0; i < 16; i += 1) {
      expect(planDeliver(realArgs, realProbe, (t) => t)).toStrictEqual(first);
    }
  });
});
