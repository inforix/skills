#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const DEFAULT_BASE_URL = "https://maritimeai-resource.openai.azure.com/openai/v1/";
const DEFAULT_MODEL = "gpt-image-2";
const DEFAULT_API_VERSION = "preview";
const DEFAULT_SIZE = "1024x1024";
const DEFAULT_QUALITY = "high";
const DEFAULT_FORMAT = "png";
const DEFAULT_TIMEOUT_MS = 180000;

function usage() {
  return `Usage:
  node imagegen/scripts/generate-image.mjs --prompt "..." [options]

Options:
  --prompt <text>          Prompt to generate from
  --prompt-file <path>     Read prompt from a UTF-8 file
  --output <path>          Output file path, or filename prefix when --n > 1
  --output-dir <path>      Directory for auto-named outputs (default: ./generated-images)
  --base-url <url>         Azure OpenAI base URL (default: AZURE_OPENAI_BASE_URL or built-in maritime endpoint)
  --model <name>           Model/deployment name (default: AZURE_OPENAI_IMAGE_MODEL or gpt-image-2)
  --size <WxH>             Image size (default: 1024x1024)
  --quality <value>        low, medium, or high (default: high)
  --format <value>         png or jpeg (default: png)
  --n <number>             Number of images, 1-10 (default: 1)
  --user <id>              Optional end-user identifier
  --timeout-ms <ms>        Request timeout in milliseconds (default: 180000)
  --dry-run                Validate and print redacted request without calling Azure
  --help                   Show this help
`;
}

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error(`Unexpected positional argument: ${token}`);
    }
    const key = token.slice(2);
    if (key === "help" || key === "dry-run") {
      args[key] = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }
    args[key] = value;
    index += 1;
  }
  return args;
}

function parseSize(size) {
  const match = /^(\d+)x(\d+)$/i.exec(size);
  if (!match) {
    throw new Error(`Invalid --size "${size}". Use WIDTHxHEIGHT, for example 1024x1024.`);
  }
  return { width: Number(match[1]), height: Number(match[2]) };
}

function validateGptImage2Size(size) {
  const { width, height } = parseSize(size);
  const longEdge = Math.max(width, height);
  const shortEdge = Math.min(width, height);
  const pixels = width * height;

  if (width % 16 !== 0 || height % 16 !== 0) {
    throw new Error("gpt-image-2 size validation failed: width and height must be multiples of 16.");
  }
  if (longEdge > 3840) {
    throw new Error("gpt-image-2 size validation failed: long edge must be <= 3840 px.");
  }
  if (longEdge / shortEdge > 3) {
    throw new Error("gpt-image-2 size validation failed: aspect ratio must be <= 3:1.");
  }
  if (pixels < 655360 || pixels > 8294400) {
    throw new Error("gpt-image-2 size validation failed: total pixels must be between 655,360 and 8,294,400.");
  }
}

function normalizeBaseUrl(baseUrl) {
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    throw new Error("Base URL is empty.");
  }
  return trimmed.endsWith("/") ? trimmed : `${trimmed}/`;
}

function timestamp() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

function extensionFor(format) {
  return format === "jpeg" ? "jpg" : "png";
}

function outputPathFor({ output, outputDir, format, index, total }) {
  const extension = extensionFor(format);
  if (!output) {
    const suffix = total > 1 ? `-${index + 1}` : "";
    return path.join(outputDir, `image-${timestamp()}${suffix}.${extension}`);
  }

  const parsed = path.parse(output);
  const hasExtension = parsed.ext.length > 0;
  if (total === 1) {
    return hasExtension ? output : `${output}.${extension}`;
  }

  const base = hasExtension ? path.join(parsed.dir, parsed.name) : output;
  return `${base}-${index + 1}.${extension}`;
}

function redactHeaders(headers) {
  return Object.fromEntries(
    Object.entries(headers).map(([key, value]) => [
      key,
      key.toLowerCase().includes("key") || key.toLowerCase() === "authorization" ? "<redacted>" : value,
    ]),
  );
}

async function buildConfig(args) {
  if (args.help) {
    return { help: true };
  }

  const promptFromFile = args["prompt-file"]
    ? (await readFile(args["prompt-file"], "utf8")).trim()
    : "";
  const prompt = (args.prompt || promptFromFile).trim();
  if (!prompt) {
    throw new Error("A prompt is required. Pass --prompt or --prompt-file.");
  }

  const apiKey = process.env.AZURE_OPENAI_API_KEY || "";
  if (!apiKey && !args["dry-run"]) {
    throw new Error("AZURE_OPENAI_API_KEY is required.");
  }

  const baseUrl = normalizeBaseUrl(
    args["base-url"] || process.env.AZURE_OPENAI_BASE_URL || DEFAULT_BASE_URL,
  );
  const model = args.model || process.env.AZURE_OPENAI_IMAGE_MODEL || DEFAULT_MODEL;
  const apiVersion = process.env.AZURE_OPENAI_API_VERSION || DEFAULT_API_VERSION;
  const size = args.size || DEFAULT_SIZE;
  const quality = args.quality || DEFAULT_QUALITY;
  const format = args.format || DEFAULT_FORMAT;
  const count = Number(args.n || 1);
  const timeoutMs = Number(args["timeout-ms"] || DEFAULT_TIMEOUT_MS);
  const outputDir = args["output-dir"] || "./generated-images";

  if (!["low", "medium", "high"].includes(quality)) {
    throw new Error("--quality must be one of: low, medium, high.");
  }
  if (!["png", "jpeg"].includes(format)) {
    throw new Error("--format must be one of: png, jpeg.");
  }
  if (!Number.isInteger(count) || count < 1 || count > 10) {
    throw new Error("--n must be an integer from 1 to 10.");
  }
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0) {
    throw new Error("--timeout-ms must be a positive integer.");
  }
  parseSize(size);
  if (model.toLowerCase() === "gpt-image-2") {
    validateGptImage2Size(size);
  }

  const body = {
    model,
    prompt,
    size,
    quality,
    n: count,
    output_format: format,
  };
  if (args.user) {
    body.user = args.user;
  }

  return {
    apiKey,
    apiVersion,
    baseUrl,
    body,
    dryRun: Boolean(args["dry-run"]),
    output: args.output,
    outputDir,
    timeoutMs,
  };
}

async function callAzure(config) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.timeoutMs);
  const url = new URL("images/generations", config.baseUrl).toString();
  const headers = {
    "Content-Type": "application/json",
    "api-key": config.apiKey,
    api_version: config.apiVersion,
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(config.body),
      signal: controller.signal,
    });

    const text = await response.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      payload = { raw: text };
    }

    if (!response.ok) {
      const message = payload?.error?.message || payload?.message || text || response.statusText;
      throw new Error(`Azure image generation failed (${response.status}): ${message}`);
    }

    return payload;
  } finally {
    clearTimeout(timeout);
  }
}

async function saveImages(payload, config) {
  const images = Array.isArray(payload.data) ? payload.data : [];
  if (images.length === 0) {
    throw new Error("Azure response did not contain any images in data[].");
  }

  const saved = [];
  for (let index = 0; index < images.length; index += 1) {
    const image = images[index];
    if (!image?.b64_json) {
      throw new Error(`Image ${index + 1} is missing b64_json.`);
    }
    const outputPath = outputPathFor({
      output: config.output,
      outputDir: config.outputDir,
      format: config.body.output_format,
      index,
      total: images.length,
    });
    await mkdir(path.dirname(outputPath), { recursive: true });
    await writeFile(outputPath, Buffer.from(image.b64_json, "base64"));
    saved.push(outputPath);
  }
  return saved;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const config = await buildConfig(args);

  if (config.help) {
    process.stdout.write(usage());
    return;
  }

  const url = new URL("images/generations", config.baseUrl).toString();
  const headers = {
    "Content-Type": "application/json",
    "api-key": config.apiKey || "<missing in dry-run>",
    api_version: config.apiVersion,
  };

  if (config.dryRun) {
    console.log(JSON.stringify({
      dryRun: true,
      url,
      headers: redactHeaders(headers),
      body: config.body,
      output: config.output || config.outputDir,
      timeoutMs: config.timeoutMs,
    }, null, 2));
    return;
  }

  const payload = await callAzure(config);
  const saved = await saveImages(payload, config);
  console.log(JSON.stringify({
    saved,
    model: config.body.model,
    size: config.body.size,
    quality: config.body.quality,
    format: config.body.output_format,
  }, null, 2));
}

main().catch((error) => {
  console.error(error?.message || String(error));
  process.exit(1);
});
