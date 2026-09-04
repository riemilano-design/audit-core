// エンジンバイナリの既定パス解決。
// apps/server/engine/ はGit管理対象外(apps/server/.gitignore参照)。
// ビルド手順は spike/README.md を参照。SHOGI_ENGINE_PATH環境変数で上書きできる。

import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const DEFAULT_ENGINE_PATH = path.join(__dirname, "..", "..", "engine", "YaneuraOu-by-gcc");

export function resolveEnginePath(): string {
  return process.env.SHOGI_ENGINE_PATH ?? DEFAULT_ENGINE_PATH;
}
