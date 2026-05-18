#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const home = process.env.HOME || '/Users/wyp';
const obsidianRegistry = path.join(home, 'Library/Application Support/obsidian/obsidian.json');
const fallbackVault = path.join(
  home,
  'Library/Mobile Documents/iCloud~md~obsidian/Documents/reader',
);

function expandHome(value) {
  if (!value) return value;
  if (value === '~') return home;
  if (value.startsWith('~/')) return path.join(home, value.slice(2));
  return value;
}

function resolveVaultPath() {
  if (process.env.READER_VAULT_PATH) {
    return path.resolve(expandHome(process.env.READER_VAULT_PATH));
  }

  try {
    const registry = JSON.parse(fs.readFileSync(obsidianRegistry, 'utf8'));
    const vaults = Object.values(registry.vaults || {});
    const readerVault = vaults.find((vault) => {
      if (!vault || typeof vault.path !== 'string') return false;
      return path.basename(vault.path) === 'reader' || vault.path.endsWith('/reader');
    });
    if (readerVault) return path.resolve(expandHome(readerVault.path));
  } catch {
    // Fall through to the stable local default.
  }

  return fallbackVault;
}

function todayInShanghai() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());
}

function slugify(input) {
  const cleaned = String(input || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/['"]/g, '')
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-');
  return cleaned || 'untitled';
}

function parseOptions(argv) {
  const options = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) {
      options._.push(token);
      continue;
    }
    const key = token.slice(2);
    if (key === 'dry-run') {
      options.dryRun = true;
      continue;
    }
    const value = argv[i + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Missing value for --${key}`);
    }
    options[key.replace(/-([a-z])/g, (_, char) => char.toUpperCase())] = value;
    i += 1;
  }
  return options;
}

function ensureFile(filePath, content, dryRun) {
  if (fs.existsSync(filePath)) {
    return { action: 'exists', path: filePath };
  }
  if (!dryRun) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf8');
  }
  return { action: dryRun ? 'would-create' : 'created', path: filePath };
}

function initVault(vaultPath, dryRun = false) {
  const dirs = ['raw', 'raw/cases', 'sources', 'topics', 'entities', 'questions', 'assets'];
  const results = [];

  for (const dir of dirs) {
    const dirPath = path.join(vaultPath, dir);
    if (fs.existsSync(dirPath)) {
      results.push({ action: 'exists', path: dirPath });
    } else {
      if (!dryRun) fs.mkdirSync(dirPath, { recursive: true });
      results.push({ action: dryRun ? 'would-create' : 'created', path: dirPath });
    }
  }

  results.push(
    ensureFile(
      path.join(vaultPath, 'index.md'),
      `# Reader Index\n\n## Sources\n\n## Topics\n\n## Entities\n\n## Questions\n`,
      dryRun,
    ),
  );
  results.push(
    ensureFile(
      path.join(vaultPath, 'log.md'),
      `# Reader Log\n\n`,
      dryRun,
    ),
  );
  results.push(
    ensureFile(
      path.join(vaultPath, 'AGENTS.md'),
      `# Reader Vault Conventions\n\n- Keep raw source captures in \`raw/\` and avoid editing them after ingest.\n- Put one source note per article, paper, report, URL, or uploaded file in \`sources/\`.\n- Update existing \`topics/\`, \`entities/\`, and \`questions/\` pages before creating near-duplicates.\n- Maintain Obsidian wiki links between pages.\n- Update \`index.md\` after every ingest and append one entry to \`log.md\`.\n`,
      `# Reader Vault Conventions\n\n- Keep raw source captures in \`raw/\` and avoid editing them after ingest.\n- Save downloaded original materials for cases mentioned by readings in \`raw/cases/<source-slug>/\`.\n- Put one source note per article, paper, report, URL, or uploaded file in \`sources/\`.\n- Update existing \`topics/\`, \`entities/\`, and \`questions/\` pages before creating near-duplicates.\n- Maintain Obsidian wiki links between pages.\n- Update \`index.md\` after every ingest and append one entry to \`log.md\`.\n`,
      dryRun,
    ),
  );

  return results;
}

function appendLog(vaultPath, options) {
  const type = options.type || 'ingest';
  const title = options.title || 'Untitled';
  const source = options.source || '';
  const pages = options.pages || '';
  const date = todayInShanghai();
  const entry = [
    `## [${date}] ${type} | ${title}`,
    source ? `- Source: ${source}` : null,
    pages ? `- Pages: ${pages}` : null,
    `- Notes: ${options.notes || 'Updated reader wiki.'}`,
    '',
  ].filter(Boolean).join('\n');

  if (!options.dryRun) {
    fs.mkdirSync(vaultPath, { recursive: true });
    fs.appendFileSync(path.join(vaultPath, 'log.md'), `${entry}\n`, 'utf8');
  }
  return entry;
}

function usage() {
  return `Usage:
  node read-article/scripts/reader-vault.mjs path
  node read-article/scripts/reader-vault.mjs init [--dry-run]
  node read-article/scripts/reader-vault.mjs slug "Article Title"
  node read-article/scripts/reader-vault.mjs log --type ingest --title "Title" --source "URL or file" --pages "sources/title.md" [--notes "..."] [--dry-run]

Environment:
  READER_VAULT_PATH  Override the detected Obsidian reader vault path.
`;
}

const [command, ...rest] = process.argv.slice(2);
const vaultPath = resolveVaultPath();

try {
  if (!command || command === 'help' || command === '--help' || command === '-h') {
    console.log(usage());
  } else if (command === 'path') {
    if (!fs.existsSync(vaultPath)) {
      console.error(`Reader vault not found: ${vaultPath}`);
      process.exitCode = 2;
    } else {
      console.log(vaultPath);
    }
  } else if (command === 'init') {
    const options = parseOptions(rest);
    const results = initVault(vaultPath, Boolean(options.dryRun));
    console.log(JSON.stringify({ vaultPath, results }, null, 2));
  } else if (command === 'slug') {
    console.log(slugify(rest.join(' ')));
  } else if (command === 'log') {
    const options = parseOptions(rest);
    console.log(appendLog(vaultPath, options));
  } else {
    console.error(`Unknown command: ${command}\n\n${usage()}`);
    process.exitCode = 2;
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
