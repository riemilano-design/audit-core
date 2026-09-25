# 06 予測の見直し(役 A = L-時間)― p4・3 分の組 18 局(2026-09-25)

**入力**: `05-H-p4-min3-001.json`・`002`・`003`(反証と `status: weak` 入り)、`04-integration.md`(統合の 4 欄)。
**変えた欄**: 3 本とも `prediction` の中(`metric`・`comparator`・`value`・`alsoRequires`)だけ。`writtenAt` は "2026-09-25" のまま。`statement`・`observations`・`counterEvidence`・`status` は同一(機械で照合)。
**閾値の数**: 「次の 20 局で測る前に決める数」として置いた。写しの値ではない数(10・0.1・2・30)は、その理由を各行に書く。
**検査**: 3 ファイルとも `hypothesisCheck --today 2026-09-25` で 9/9 ok。

---

## H-p4-min3-001(段ごとの消費の中央値) ― 変更あり

| 欄 | 前 | 後 |
|---|---|---|
| metric | `groupMedians[3 分].timeUpLoss.medianMidSec − other.medianMidSec` | 同じ |
| comparator / value | `> 0` | `>= 10`(秒) |
| alsoRequires | `timeUpLoss.games >= 3`、`other.games >= 5` | `timeUpLoss.games >= 5`、`other.games >= 10` |

理由: 反証の denominator(5 局の中央値は局 11 の 1 局の値。最小 3 局ではさらに 1 局の値)を受け、分母の下限を今回の実測(5 局・13 局)に近い 5 局・10 局へ上げた。反証の counterexample(中)で局ごとの値に重なり(それ以外の局 10 が 76 秒・局 4 が 69 秒、時間で負けた局の 68・66 秒を上回る)があるため、`> 0` では 1 局の入れ替わりで動く。今回の差 68 − 51 = 17 秒の半分強にあたる 10 秒を幅として置いた。統合の未確認のうち「使った時間の合計で言い換えられる」「手数あたりでは並びが変わる」は、写しの `groupMedians` に手数あたりの中央値の欄が無く、この予測の物差しでは分けられない(未確認のまま残る)。

## H-p4-min3-002(消費の段ごとの崩れの割合) ― 変更あり

| 欄 | 前 | 後 |
|---|---|---|
| metric | `bySpent[2].collapsed / bySpent[2].n − bySpent[0].collapsed / bySpent[0].n` | 同じ |
| comparator / value | `> 0` | `>= 0.1`(割合の差 = 10 ポイント) |
| alsoRequires | `bySpent[2].n >= 20`、`bySpent[0].n >= 20` | `bySpent[2].n >= 30`、`bySpent[0].n >= 30` |

理由: 反証の denominator(32 組 対 88 組で分母が違い、崩れ 10 組が何局に分かれるかは追えない)と counterexample(最も長い段 8 組は崩れ 0 組で向きが逆)を受け、`> 0` では崩れ 1 組の出入りで動くため、割合の差に 10 ポイントの幅を置いた(今回の差は 10/32 と 3/88 の差でおよそ 28 ポイント。その半分以下で、かつ 1〜2 組の出入りでは越えない大きさ)。分母の下限は今回の [2] の 32 組に近い 30 組へ上げ、[0] も同じ 30 組に揃えた(満たさなければ「測れず」)。統合の未確認のうち「段(序・中・終)や分かれ道の印で説明がつく」は、組と局・手の対応が写しに無いためこの物差しでは分けられない(未確認のまま残る)。

## H-p4-min3-003(長考の回数などの中央値) ― 変更あり

| 欄 | 前 | 後 |
|---|---|---|
| metric | `groupMedians[3 分].timeUpLoss.medianLongThinkTotal − other.medianLongThinkTotal` | 同じ |
| comparator / value | `> 0` | `>= 2`(回) |
| alsoRequires | `timeUpLoss.games >= 3`、`other.games >= 5` | `timeUpLoss.games >= 5`、`other.games >= 10` |

理由: 反証の counterexample(長考の回数で時間で負けた局 14・16 の 3 回が、それ以外の局 3・8・10 の 3 回と同じ値)と denominator(5 局のうち 2 局はそれ以外の側に近く、3 局だけで中央値が決まりうる)を受け、分母の下限を 5 局・10 局へ上げ、回数は整数なので `> 0` を 1 回の差で越えないよう、今回の差(4 − 2 = 2 回)と同じ 2 回を幅として置いた。物差しは 3 つの中央値のうち長考の回数 1 つだけなので、反証の alternative(3 つは同じ手の 3 通りの数え方)には元から依らない。「使った時間の合計で説明がつく」はこの物差しでは分けられない(未確認のまま残る)。
