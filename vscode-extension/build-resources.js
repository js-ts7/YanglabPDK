const fs = require("fs");
const path = require("path");

const extensionRoot = __dirname;
const packageRoot = path.resolve(extensionRoot, "..");
const resources = path.join(extensionRoot, "resources");
const sourceManifest = path.join(packageRoot, "catalog", "components.json");
const sourceThumbnails = path.join(packageRoot, "catalog_assets", "thumbnails");

fs.mkdirSync(resources, { recursive: true });
if (!fs.existsSync(sourceManifest)) {
  throw new Error(`Catalog manifest not found: ${sourceManifest}`);
}
fs.copyFileSync(sourceManifest, path.join(resources, "components.json"));

const targetThumbnails = path.join(resources, "thumbnails");
fs.rmSync(targetThumbnails, { recursive: true, force: true });
fs.mkdirSync(targetThumbnails, { recursive: true });
if (fs.existsSync(sourceThumbnails)) {
  for (const entry of fs.readdirSync(sourceThumbnails, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.toLowerCase().endsWith(".png")) {
      fs.copyFileSync(path.join(sourceThumbnails, entry.name), path.join(targetThumbnails, entry.name));
    }
  }
}

console.log(`Prepared extension resources in ${resources}`);
