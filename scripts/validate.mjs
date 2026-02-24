#!/usr/bin/env node
/**
 * Zero-dependency validation script for Actant component hubs.
 * Validates manifest, component schemas, SKILL.md frontmatter,
 * file references, and cross-component consistency.
 *
 * Usage: node scripts/validate.mjs [--strict] [rootDir]
 */
import { readFile, readdir, stat, access } from "node:fs/promises";
import { join, relative, extname, resolve } from "node:path";

// ---------------------------------------------------------------------------
// Issue collector
// ---------------------------------------------------------------------------

const issues = [];

function addIssue(severity, path, message, code, component) {
  issues.push({ severity, path, message, code, component });
}

// ---------------------------------------------------------------------------
// YAML frontmatter parser (minimal, no dependencies)
// ---------------------------------------------------------------------------

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;

  const fields = {};
  for (const line of match[1].split("\n")) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let val = line.slice(idx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (key && !key.startsWith(" ")) {
      fields[key] = val;
    }
  }
  return fields;
}

// ---------------------------------------------------------------------------
// File helpers
// ---------------------------------------------------------------------------

async function fileExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function readJson(path) {
  const raw = await readFile(path, "utf-8");
  return JSON.parse(raw);
}

// ---------------------------------------------------------------------------
// Validators
// ---------------------------------------------------------------------------

const REQUIRED_MANIFEST_FIELDS = ["name", "version", "components"];
const COMPONENT_TYPES = ["skills", "prompts", "mcp", "templates"];
const REQUIRED_COMPONENT_FIELDS = {
  skills: ["name", "version", "description", "content"],
  prompts: ["name", "version", "description", "content"],
  mcp: ["name", "version", "description", "command"],
  templates: ["name", "version", "description", "backend"],
  presets: ["name", "version", "description"],
};
const REQUIRED_SKILL_MD_FIELDS = ["name", "description"];

async function validateManifest(rootDir) {
  const manifestPath = join(rootDir, "actant.json");
  if (!(await fileExists(manifestPath))) {
    addIssue("error", "actant.json", "actant.json not found in source root", "MANIFEST_MISSING");
    return null;
  }

  let manifest;
  try {
    manifest = await readJson(manifestPath);
  } catch (err) {
    addIssue("error", "actant.json", `Invalid JSON: ${err.message}`, "MANIFEST_INVALID_JSON");
    return null;
  }

  for (const field of REQUIRED_MANIFEST_FIELDS) {
    if (!(field in manifest)) {
      addIssue("error", "actant.json", `Missing required field: "${field}"`, "MANIFEST_FIELD_MISSING");
    }
  }

  if (typeof manifest.name !== "string" || manifest.name.length === 0) {
    addIssue("error", "actant.json", '"name" must be a non-empty string', "MANIFEST_INVALID_NAME");
  }
  if (typeof manifest.version !== "string" || !/^\d+\.\d+\.\d+/.test(manifest.version)) {
    addIssue("error", "actant.json", '"version" must be a valid semver string', "MANIFEST_INVALID_VERSION");
  }

  return manifest;
}

async function validateManifestFileRefs(rootDir, manifest) {
  const allRefs = [];

  if (manifest.components) {
    for (const [type, files] of Object.entries(manifest.components)) {
      if (Array.isArray(files)) {
        for (const f of files) allRefs.push({ ref: f, section: `components.${type}` });
      }
    }
  }
  if (Array.isArray(manifest.presets)) {
    for (const f of manifest.presets) allRefs.push({ ref: f, section: "presets" });
  }

  for (const { ref, section } of allRefs) {
    if (!(await fileExists(join(rootDir, ref)))) {
      addIssue("error", "actant.json", `File referenced in ${section} does not exist: ${ref}`, "MANIFEST_FILE_MISSING", ref);
    }
  }
}

async function validateComponentFile(rootDir, relPath, componentType) {
  const fullPath = join(rootDir, relPath);
  let data;
  try {
    data = await readJson(fullPath);
  } catch (err) {
    addIssue("error", relPath, `Invalid JSON: ${err.message}`, "INVALID_JSON");
    return null;
  }

  const required = REQUIRED_COMPONENT_FIELDS[componentType];
  if (required) {
    for (const field of required) {
      if (!(field in data)) {
        addIssue("error", relPath, `Missing required field: "${field}"`, "COMPONENT_FIELD_MISSING", data.name);
      }
    }
  }

  if (data.name && typeof data.name !== "string") {
    addIssue("error", relPath, '"name" must be a string', "COMPONENT_INVALID_NAME", data.name);
  }

  return data;
}

async function validateSkillMd(rootDir, relPath) {
  const fullPath = join(rootDir, relPath);
  let raw;
  try {
    raw = await readFile(fullPath, "utf-8");
  } catch {
    addIssue("error", relPath, "Cannot read SKILL.md file", "FILE_UNREADABLE");
    return null;
  }

  const fm = parseFrontmatter(raw);
  if (!fm) {
    addIssue("error", relPath, "Missing YAML frontmatter (expected --- delimiters)", "SKILL_MD_NO_FRONTMATTER");
    return null;
  }

  for (const field of REQUIRED_SKILL_MD_FIELDS) {
    if (!fm[field]) {
      addIssue("error", relPath, `Missing required frontmatter field: "${field}"`, "SKILL_MD_FIELD_MISSING", fm.name);
    }
  }

  const frontmatterEnd = raw.indexOf("---", 3);
  if (frontmatterEnd !== -1) {
    const body = raw.substring(frontmatterEnd + 3).trim();
    if (body.length === 0) {
      addIssue("warning", relPath, "SKILL.md has empty content body", "SKILL_MD_EMPTY_CONTENT", fm.name);
    }
  }

  return fm;
}

async function validateRegistryJson(rootDir, componentNames) {
  const registryPath = join(rootDir, "registry.json");
  if (!(await fileExists(registryPath))) {
    addIssue("warning", "registry.json", "registry.json not found (optional but recommended)", "REGISTRY_MISSING");
    return;
  }

  let registry;
  try {
    registry = await readJson(registryPath);
  } catch (err) {
    addIssue("error", "registry.json", `Invalid JSON: ${err.message}`, "REGISTRY_INVALID_JSON");
    return;
  }

  if (!registry.components) {
    addIssue("warning", "registry.json", 'Missing "components" section', "REGISTRY_NO_COMPONENTS");
    return;
  }

  const typeMap = { skills: "skills", prompts: "prompts", mcp: "mcp", templates: "templates", presets: "presets" };
  for (const [regType, compType] of Object.entries(typeMap)) {
    const regComponents = registry.components[regType];
    if (!Array.isArray(regComponents)) continue;
    const knownNames = componentNames.get(compType) ?? new Set();
    for (const comp of regComponents) {
      if (comp.name && !knownNames.has(comp.name)) {
        addIssue("warning", "registry.json", `Registry lists ${regType} "${comp.name}" which is not in actant.json`, "REGISTRY_UNKNOWN_COMPONENT", comp.name);
      }
    }
  }
}

async function validatePresetReferences(rootDir, manifest, componentNames) {
  const presetFiles = manifest?.presets ?? [];
  for (const presetFile of presetFiles) {
    const fullPath = join(rootDir, presetFile);
    let data;
    try {
      data = await readJson(fullPath);
    } catch {
      continue;
    }

    const refMap = [
      ["skills", "skills"],
      ["prompts", "prompts"],
      ["mcpServers", "mcp"],
      ["templates", "templates"],
    ];

    for (const [field, compType] of refMap) {
      const refs = data[field];
      if (!Array.isArray(refs)) continue;
      const available = componentNames.get(compType) ?? new Set();
      for (const ref of refs) {
        if (!available.has(ref)) {
          addIssue("warning", presetFile, `Preset "${data.name}" references ${compType} "${ref}" not found in source`, "PRESET_REF_MISSING", data.name);
        }
      }
    }
  }
}

async function validateSkillMdJsonConsistency(rootDir, manifest) {
  const skillJsonFiles = manifest?.components?.skills ?? [];
  for (const jsonPath of skillJsonFiles) {
    const skillName = jsonPath.replace(/^skills\//, "").replace(/\.json$/, "");
    const mdPath = `skills/${skillName}/SKILL.md`;
    const jsonFull = join(rootDir, jsonPath);
    const mdFull = join(rootDir, mdPath);

    if ((await fileExists(jsonFull)) && (await fileExists(mdFull))) {
      const jsonData = await readJson(jsonFull).catch(() => null);
      const mdRaw = await readFile(mdFull, "utf-8").catch(() => null);
      if (jsonData && mdRaw) {
        const fm = parseFrontmatter(mdRaw);
        if (fm && fm.name !== jsonData.name) {
          addIssue("warning", mdPath, `SKILL.md name "${fm.name}" differs from JSON name "${jsonData.name}"`, "SKILL_NAME_MISMATCH", fm.name);
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const args = process.argv.slice(2);
  const strict = args.includes("--strict");
  const rootDir = resolve(args.find((a) => !a.startsWith("--")) ?? ".");

  console.log(`\n🔍 Validating Actant hub: ${rootDir}`);
  console.log(`   Mode: ${strict ? "strict" : "normal"}\n`);

  const componentNames = new Map();
  let passCount = 0;

  // 1. Manifest
  const manifest = await validateManifest(rootDir);
  if (manifest) {
    passCount++;
    await validateManifestFileRefs(rootDir, manifest);
  }

  // 2. Component files (from manifest)
  if (manifest?.components) {
    for (const [type, files] of Object.entries(manifest.components)) {
      if (!Array.isArray(files)) continue;
      for (const filePath of files) {
        const data = await validateComponentFile(rootDir, filePath, type);
        if (data?.name) {
          if (!componentNames.has(type)) componentNames.set(type, new Set());
          componentNames.get(type).add(data.name);
          passCount++;
        }
      }
    }
  }

  // 3. Presets (from manifest)
  if (Array.isArray(manifest?.presets)) {
    for (const filePath of manifest.presets) {
      const data = await validateComponentFile(rootDir, filePath, "presets");
      if (data?.name) {
        if (!componentNames.has("presets")) componentNames.set("presets", new Set());
        componentNames.get("presets").add(data.name);
        passCount++;
      }
    }
  }

  // 4. SKILL.md files
  const skillsDir = join(rootDir, "skills");
  try {
    const entries = await readdir(skillsDir);
    for (const entry of entries) {
      const entryPath = join(skillsDir, entry);
      const s = await stat(entryPath).catch(() => null);
      if (s?.isDirectory()) {
        const mdPath = join(entryPath, "SKILL.md");
        if (await fileExists(mdPath)) {
          const relPath = relative(rootDir, mdPath).replace(/\\/g, "/");
          const fm = await validateSkillMd(rootDir, relPath);
          if (fm?.name) passCount++;
        }
      }
    }
  } catch {
    /* no skills directory */
  }

  // 5. Cross-reference checks
  await validatePresetReferences(rootDir, manifest, componentNames);
  await validateSkillMdJsonConsistency(rootDir, manifest);
  await validateRegistryJson(rootDir, componentNames);

  // Report
  const errors = issues.filter((i) => i.severity === "error");
  const warnings = issues.filter((i) => i.severity === "warning");
  const valid = strict ? errors.length === 0 && warnings.length === 0 : errors.length === 0;

  console.log("─".repeat(60));
  if (errors.length > 0) {
    console.log("\n❌ Errors:");
    for (const i of errors) {
      console.log(`  [${i.code}] ${i.path}: ${i.message}`);
    }
  }
  if (warnings.length > 0) {
    console.log("\n⚠️  Warnings:");
    for (const i of warnings) {
      console.log(`  [${i.code}] ${i.path}: ${i.message}`);
    }
  }

  console.log("\n─".repeat(60));
  console.log(`\n📊 Results: ${passCount} passed, ${errors.length} errors, ${warnings.length} warnings`);
  console.log(`   Status: ${valid ? "✅ PASS" : "❌ FAIL"}\n`);

  if (!valid) process.exit(1);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
