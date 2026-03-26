---
name: electronic-trusted-certificate
description: Use this skill whenever the user mentions 电子可信证明,成绩单,在读证明,绩点证明 electronic trusted certificates, student proof documents, enrollment or study-status certificates, transcript or degree verification, verification codes, or asks to use the SHMTU MCP server over HTTP. This skill probes the endpoint, initializes the MCP session, lists tools, and calls the right tool with bearer-token authentication without writing secrets into repo files.
---

# Electronic Trusted Certificate

Use this skill to work with the SHMTU electronic trusted certificate MCP service over HTTP.

## What To Collect

- `endpoint`: default to the user-provided MCP HTTP endpoint.
- `token`: use a bearer token from the user or from an environment variable.
- `goal`: what certificate or proof the user wants to query, generate, download, or verify.
- `output_path`: only needed when the server returns a downloadable file and the user wants it saved locally.

## Secret Handling

- Never write real tokens into tracked files.
- Prefer environment variables for local execution:

```bash
export SHMTU_CERT_MCP_ENDPOINT='https://jwxt.shmtu.edu.cn/info/mcp'
export SHMTU_CERT_MCP_TOKEN='replace-with-real-token'
```

- If the user already provided a token in the conversation, use it only for the current terminal session.

## Default Workflow

1. Probe the endpoint before assuming the path is correct:

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs probe
```

2. Discover available tools and inspect the returned schema:

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs list-tools
```

3. Pick the tool that best matches the user request. Prefer exact matches such as certificate lookup, download, verification, transcript proof, or study-status proof.

4. Call the tool with the minimum valid argument set:

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs call-tool \
  --tool TOOL_NAME \
  --arguments-json '{"example":"value"}'
```

5. If the result contains a file URL, save it with `curl -L`. If it contains base64 data, decode it into the requested output file. If it returns plain JSON, summarize the important fields and keep the raw JSON if the user needs auditing.

6. In the final response, report:
- which endpoint was used
- which tool was called
- which arguments were sent, with secrets redacted
- where any downloaded file was saved
- any unresolved server-side or schema-side errors

## Command Reference

### Probe the endpoint

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs probe \
  --endpoint "$SHMTU_CERT_MCP_ENDPOINT" \
  --token "$SHMTU_CERT_MCP_TOKEN"
```

If Node cannot validate the remote certificate chain but `curl` works, retry with `--insecure` for a one-off probe or provide `--ca-file <pem-bundle>`.

### Initialize only

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs initialize \
  --endpoint "$SHMTU_CERT_MCP_ENDPOINT" \
  --token "$SHMTU_CERT_MCP_TOKEN"
```

### List tools

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs list-tools \
  --endpoint "$SHMTU_CERT_MCP_ENDPOINT" \
  --token "$SHMTU_CERT_MCP_TOKEN"
```

### Call a tool

```bash
node electronic-trusted-certificate/scripts/http_mcp.mjs call-tool \
  --endpoint "$SHMTU_CERT_MCP_ENDPOINT" \
  --token "$SHMTU_CERT_MCP_TOKEN" \
  --tool TOOL_NAME \
  --arguments-json '{"student_id":"20240001"}'
```

## Decision Rules

- Always run `list-tools` before the first real tool call in a session unless the tool schema is already known from the immediately preceding step.
- Do not invent argument names. Copy them from the tool schema.
- If the endpoint returns `404`, treat the supplied URL as unresolved and tell the user the current path does not exist from this environment.
- If the endpoint returns `401` or `403`, treat the token as missing, expired, or unauthorized.
- If the server returns validation errors, reduce the payload to the required fields and try again once.
- If the user asks for a document but the MCP tool only returns metadata or a verification URL, report that explicitly instead of pretending the file was downloaded.

## Output Handling

- For JSON responses, keep the raw structure intact and summarize only the key fields the user asked about.
- For arrays of mixed content blocks, preserve order and type. Save text blocks as UTF-8 text. Save binary payloads only after confirming their encoding.
- For returned URLs, prefer `curl -L -o <absolute-path> '<url>'`.
- For base64 payloads, decode with a local command and keep the file extension consistent with the returned MIME type or filename.

## Troubleshooting

- `404 Not Found`: the endpoint path is wrong or not exposed from the current network path.
- `405 Method Not Allowed`: the server exists but expects a different HTTP method.
- `401` or `403`: token problem.
- JSON-RPC parse error: request body shape or content type is wrong.
- MCP schema mismatch: rerun `list-tools`, then compare the tool input schema against the arguments being sent.
- TLS verification failure in Node: retry with `--insecure` for local debugging or provide `--ca-file` with the correct issuer bundle.

## Notes

- The helper script uses only built-in Node.js modules.
- It automatically sends `initialize`, `notifications/initialized`, and the follow-up request for `list-tools` and `call-tool`.
- If the server responds with `text/event-stream`, the helper script extracts `data:` frames and prints them as parsed JSON when possible.
