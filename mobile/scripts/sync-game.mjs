import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const htmlFile = resolve(mobileRoot, "../index.html");
const outputFile = resolve(mobileRoot, "src/game.generated.ts");
const source = readFileSync(htmlFile, "utf8");
const output = "// AUTO-GENERATED from ../../index.html. Run npm run sync:game.\n" +
  "export const GAME_HTML: string = " + JSON.stringify(source) + ";\n";
if (process.argv.includes("--check")) {
  if (readFileSync(outputFile, "utf8") !== output) {
    console.error("Bundled arcade HTML is stale. Run npm run sync:game and commit the result.");
    process.exit(1);
  }
  console.log("Bundled arcade game matches root index.html.");
} else {
  writeFileSync(outputFile, output);
  console.log("Refreshed mobile/src/game.generated.ts from root index.html");
}
