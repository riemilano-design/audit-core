# NNUE 版の固定棋譜 7 局の記録(STEP D0-NNUE、2026-09-14〜15)

`replay.ts --nodes 4000000 --threads 1` で固定棋譜 7 局(`scripts/playtest/kifu/`)を再生した JSONL。校正(U6-T の `CALIBRATION_BASELINE.source`)と診断(D1)の材料として、**消えない場所に置くためにコミットした**。`out/` は gitignore 対象で残らないため。記録は観測であり、何も拘束しない。

- 評価関数: 水匠 5(`apps/server/engine/nnue/eval/nn.bin`、sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、64,217,066 バイト)。**`meta` 行には残らない**(既知事項 P-43)
- エンジン: `apps/server/engine/nnue/YaneuraOu-by-gcc`(sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、clone HEAD `c1b80eaa`、`id name YaneuraOu NNUE 9.80git 64APPLEM1` は担当 C の観測)。`FV_SCALE 24`(`eval/eval_options.txt`)
- 記録時の HEAD `a9da058`・dirty false。ready 107 行、`engineReference` null 1 行(`claude-2-round2` ply 30 の王手中。作りどおり)
- 特別値: `claude-3-round2` ply 30 の `afterPass.scoreCp 35281` は評価値でない(既知事項 P-45)
- 詳細は [docs/STEP_D0-NNUE_PLAN_2026-09-14.md](../../../../docs/STEP_D0-NNUE_PLAN_2026-09-14.md) 6.11。`SHA256SUMS` は C の worktree の原本と一致することを司令塔が確かめた
