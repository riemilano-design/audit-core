// エンジン疎通スモークテスト(docs/TESTING_STRATEGY.md 4番)。
// やねうら王プロセスが起動し、usi->usiok / isready->readyok が一定時間内に
// 返ることだけを確認する。CIやローカル環境差(エンジンのパス等)で失敗しやすいため、
// 他の(バイナリ不要な)テストとは別ファイルに分離している。
//
// エンジンバイナリはGit管理対象外(apps/server/.gitignoreでengine/を除外)。
// ビルド手順はspike/README.mdを参照し、apps/server/engine/ に配置するか、
// SHOGI_ENGINE_PATH 環境変数でパスを指定すること。
// バイナリが見つからない環境ではこのテストをスキップする。

import { existsSync } from "node:fs";
import { describe, it } from "vitest";
import { resolveEnginePath } from "./enginePath.js";
import { UsiEngine } from "./usiEngine.js";

const ENGINE_PATH = resolveEnginePath();
const engineAvailable = existsSync(ENGINE_PATH);

if (!engineAvailable) {
  console.warn(
    `[usiEngine.smoke.test] エンジンバイナリが見つからないためスキップします: ${ENGINE_PATH}\n` +
      "  ビルド手順は spike/README.md を参照してください。",
  );
}

describe.skipIf(!engineAvailable)("UsiEngine (エンジン疎通スモークテスト)", () => {
  it(
    "usi->usiok / isready->readyok のハンドシェイクが一定時間内に返る",
    async () => {
      const engine = new UsiEngine(ENGINE_PATH);
      engine.start();
      try {
        await engine.usiHandshake();
        await engine.isReady();
      } finally {
        engine.quit();
        engine.close();
      }
    },
    15_000,
  );
});
