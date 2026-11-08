// WebKit入力層のみ。実機SafariやWASMの成功を意味しない。
process.argv.push("--webkit","--controls-only");
require("./smoke_comparison_web.cjs");
