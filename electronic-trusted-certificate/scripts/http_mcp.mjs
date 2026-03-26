#!/usr/bin/env node

import fs from "node:fs";
import https from "node:https";
import { URL } from "node:url";

const DEFAULT_PROTOCOL_VERSION = "2024-11-05";
const USER_AGENT = "electronic-trusted-certificate-skill/1.0";

function fail(message) {
  console.error(message);
  process.exit(1);
}

function parseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function parseSse(text) {
  const events = [];
  let buffer = [];

  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith("data:")) {
      buffer.push(line.slice(5).trimStart());
      continue;
    }
    if (!line.trim() && buffer.length > 0) {
      events.push(buffer.join("\n"));
      buffer = [];
    }
  }

  if (buffer.length > 0) {
    events.push(buffer.join("\n"));
  }

  return events.map(parseJson);
}

function formatBody(headers, bodyText) {
  const contentType = headers["content-type"] || "";
  if (contentType.includes("text/event-stream") || bodyText.includes("data:")) {
    return {
      format: "sse",
      events: parseSse(bodyText),
    };
  }
  return parseJson(bodyText);
}

function buildAgent(options) {
  const agentOptions = {};
  if (options.insecure) {
    agentOptions.rejectUnauthorized = false;
  }
  if (options.caFile) {
    agentOptions.ca = fs.readFileSync(options.caFile, "utf8");
  }
  return new https.Agent(agentOptions);
}

async function request(endpoint, { method, token, payload, timeout, extraHeaders, agent }) {
  const headers = {
    Accept: "application/json, text/event-stream",
    "User-Agent": USER_AGENT,
    ...extraHeaders,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let body;
  if (payload !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(payload);
  }

  const url = new URL(endpoint);

  return await new Promise((resolve) => {
    const req = https.request(
      {
        protocol: url.protocol,
        hostname: url.hostname,
        port: url.port || 443,
        path: `${url.pathname}${url.search}`,
        method,
        headers,
        agent,
      },
      (response) => {
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf8");
          const responseHeaders = {};
          for (const [key, value] of Object.entries(response.headers)) {
            responseHeaders[key] = Array.isArray(value) ? value.join(", ") : (value ?? "");
          }
          resolve({
            status: response.statusCode ?? null,
            headers: responseHeaders,
            body: formatBody(responseHeaders, raw),
          });
        });
      },
    );

    req.setTimeout(timeout * 1000, () => {
      req.destroy(new Error(`Request timed out after ${timeout} seconds`));
    });

    req.on("error", (error) => {
      resolve({
        status: null,
        headers: {},
        body: { error: String(error.message || error) },
      });
    });

    if (body !== undefined) {
      req.write(body);
    }
    req.end();
  });
}

function rpcPayload(requestId, method, params) {
  const payload = {
    jsonrpc: "2.0",
    id: requestId,
    method,
  };
  if (params !== undefined) {
    payload.params = params;
  }
  return payload;
}

function initializeParams(options) {
  return {
    protocolVersion: options.protocolVersion,
    capabilities: {},
    clientInfo: {
      name: options.clientName,
      version: options.clientVersion,
    },
  };
}

function mcpSessionId(headers) {
  for (const [key, value] of Object.entries(headers)) {
    if (key.toLowerCase() === "mcp-session-id") {
      return value;
    }
  }
  return null;
}

function printJson(data) {
  console.log(JSON.stringify(data, null, 2));
}

async function runProbe(options) {
  const agent = buildAgent(options);
  const initialize = rpcPayload(1, "initialize", initializeParams(options));
  const results = [
    {
      request: { method: "GET" },
      response: await request(options.endpoint, {
        method: "GET",
        token: options.token,
        timeout: options.timeout,
        agent,
      }),
    },
    {
      request: { method: "OPTIONS" },
      response: await request(options.endpoint, {
        method: "OPTIONS",
        token: options.token,
        timeout: options.timeout,
        agent,
      }),
    },
    {
      request: { method: "POST", payload: initialize },
      response: await request(options.endpoint, {
        method: "POST",
        token: options.token,
        payload: initialize,
        timeout: options.timeout,
        agent,
      }),
    },
  ];
  printJson(results);
}

async function runInitialize(options) {
  const agent = buildAgent(options);
  const response = await request(options.endpoint, {
    method: "POST",
    token: options.token,
    payload: rpcPayload(1, "initialize", initializeParams(options)),
    timeout: options.timeout,
    agent,
  });
  response.session_id = mcpSessionId(response.headers);
  printJson(response);
}

async function initializeAndNotify(options) {
  const agent = buildAgent(options);
  const initializeResponse = await request(options.endpoint, {
    method: "POST",
    token: options.token,
    payload: rpcPayload(1, "initialize", initializeParams(options)),
    timeout: options.timeout,
    agent,
  });
  const sessionId = mcpSessionId(initializeResponse.headers);
  if (initializeResponse.status === null || initializeResponse.status >= 400) {
    return { initializeResponse, sessionId, agent };
  }

  const extraHeaders = sessionId ? { "Mcp-Session-Id": sessionId } : {};
  await request(options.endpoint, {
    method: "POST",
    token: options.token,
    payload: { jsonrpc: "2.0", method: "notifications/initialized" },
    timeout: options.timeout,
    extraHeaders,
    agent,
  });

  return { initializeResponse, sessionId, agent };
}

function requireArgumentsJson(raw) {
  const value = parseJson(raw);
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    fail("--arguments-json must decode to a JSON object");
  }
  return value;
}

async function runListTools(options) {
  const { initializeResponse, sessionId, agent } = await initializeAndNotify(options);
  if (initializeResponse.status === null || initializeResponse.status >= 400) {
    printJson({
      initialize: initializeResponse,
      error: "Initialization failed; tools/list was not attempted.",
    });
    return;
  }

  const extraHeaders = sessionId ? { "Mcp-Session-Id": sessionId } : {};
  const toolsResponse = await request(options.endpoint, {
    method: "POST",
    token: options.token,
    payload: rpcPayload(2, "tools/list", {}),
    timeout: options.timeout,
    extraHeaders,
    agent,
  });

  printJson({
    initialize: initializeResponse,
    session_id: sessionId,
    tools_list: toolsResponse,
  });
}

async function runCallTool(options) {
  const { initializeResponse, sessionId, agent } = await initializeAndNotify(options);
  if (initializeResponse.status === null || initializeResponse.status >= 400) {
    printJson({
      initialize: initializeResponse,
      error: "Initialization failed; tools/call was not attempted.",
    });
    return;
  }

  const extraHeaders = sessionId ? { "Mcp-Session-Id": sessionId } : {};
  const toolResponse = await request(options.endpoint, {
    method: "POST",
    token: options.token,
    payload: rpcPayload(2, "tools/call", {
      name: options.tool,
      arguments: requireArgumentsJson(options.argumentsJson),
    }),
    timeout: options.timeout,
    extraHeaders,
    agent,
  });

  printJson({
    initialize: initializeResponse,
    session_id: sessionId,
    tool_call: toolResponse,
  });
}

function parseArgs(argv) {
  const args = {
    endpoint: process.env.SHMTU_CERT_MCP_ENDPOINT,
    token: process.env.SHMTU_CERT_MCP_TOKEN,
    timeout: 30,
    protocolVersion: DEFAULT_PROTOCOL_VERSION,
    clientName: "codex-electronic-trusted-certificate",
    clientVersion: "1.0",
    insecure: false,
    caFile: undefined,
    tool: undefined,
    argumentsJson: undefined,
  };

  if (argv.length === 0) {
    return { command: null, options: args };
  }

  if (argv[0] === "-h" || argv[0] === "--help") {
    return { command: "help", options: args };
  }

  const [command, ...rest] = argv;
  for (let i = 0; i < rest.length; i += 1) {
    const current = rest[i];
    const next = rest[i + 1];

    switch (current) {
      case "--endpoint":
        args.endpoint = next;
        i += 1;
        break;
      case "--token":
        args.token = next;
        i += 1;
        break;
      case "--timeout":
        args.timeout = Number(next);
        i += 1;
        break;
      case "--protocol-version":
        args.protocolVersion = next;
        i += 1;
        break;
      case "--client-name":
        args.clientName = next;
        i += 1;
        break;
      case "--client-version":
        args.clientVersion = next;
        i += 1;
        break;
      case "--ca-file":
        args.caFile = next;
        i += 1;
        break;
      case "--tool":
        args.tool = next;
        i += 1;
        break;
      case "--arguments-json":
        args.argumentsJson = next;
        i += 1;
        break;
      case "--insecure":
        args.insecure = true;
        break;
      case "-h":
      case "--help":
        return { command: "help", options: args };
      default:
        fail(`Unknown argument: ${current}`);
    }
  }

  return { command, options: args };
}

function printHelp() {
  console.log(`Usage: node electronic-trusted-certificate/scripts/http_mcp.mjs <command> [options]

Commands:
  probe         Probe the endpoint with GET, OPTIONS, and POST initialize.
  initialize    Send only the initialize request.
  list-tools    Initialize, notify, then request tools/list.
  call-tool     Initialize, notify, then request tools/call.

Options:
  --endpoint <url>             MCP HTTP endpoint. Defaults to $SHMTU_CERT_MCP_ENDPOINT
  --token <token>              Bearer token. Defaults to $SHMTU_CERT_MCP_TOKEN
  --timeout <seconds>          HTTP timeout in seconds. Default: 30
  --protocol-version <value>   MCP protocol version. Default: ${DEFAULT_PROTOCOL_VERSION}
  --client-name <value>        Client name for initialize
  --client-version <value>     Client version for initialize
  --ca-file <path>             PEM bundle to trust for TLS
  --insecure                   Disable TLS certificate verification
  --tool <name>                Tool name for call-tool
  --arguments-json <json>      JSON object for tool arguments
  -h, --help                   Show this help text`);
}

async function main() {
  const { command, options } = parseArgs(process.argv.slice(2));

  if (!command || command === "help") {
    printHelp();
    process.exit(command === "help" ? 0 : 1);
  }

  if (!options.endpoint) {
    fail("Missing endpoint. Pass --endpoint or set SHMTU_CERT_MCP_ENDPOINT.");
  }

  switch (command) {
    case "probe":
      await runProbe(options);
      break;
    case "initialize":
      await runInitialize(options);
      break;
    case "list-tools":
      await runListTools(options);
      break;
    case "call-tool":
      if (!options.tool) {
        fail("Missing --tool.");
      }
      if (!options.argumentsJson) {
        fail("Missing --arguments-json.");
      }
      await runCallTool(options);
      break;
    default:
      fail(`Unknown command: ${command}`);
  }
}

await main();
