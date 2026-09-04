import { defineConfig } from "vite";

// apps/server(既定でport 3000)への/apiプロキシ。開発時のみ使う設定。
export default defineConfig({
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
    },
  },
});
