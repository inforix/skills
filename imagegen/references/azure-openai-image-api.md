# Azure OpenAI Image API Notes

## Endpoint Variants

Preferred configured endpoint:

```text
https://maritimeai-resource.openai.azure.com/openai/v1/
```

The CLI appends `images/generations` to this base URL and sends a JSON POST request.

Older Azure OpenAI examples may use a deployment-style URL:

```text
https://<resource>.openai.azure.com/openai/deployments/<deployment>/images/generations?api-version=<version>
```

Use the configured `/openai/v1/` base URL first. If Azure returns route or API-version errors, compare the resource deployment settings and current Azure docs before changing the skill.

## Authentication

Use the API key from `AZURE_OPENAI_API_KEY`. The CLI sends:

- `Content-Type: application/json`
- `api-key: <redacted>`
- `api_version: preview` unless overridden by `AZURE_OPENAI_API_VERSION`

Never persist the API key in skill files.

## Request Body

Typical body:

```json
{
  "model": "gpt-image-2",
  "prompt": "A watercolor painting of a maritime research vessel at sunrise",
  "size": "1024x1024",
  "quality": "high",
  "n": 1,
  "output_format": "png"
}
```

Optional fields include `user`. The CLI omits null or empty optional fields.

## Response Handling

The image response is expected to contain:

```json
{
  "data": [
    { "b64_json": "<base64 image data>" }
  ]
}
```

Decode `b64_json` and save bytes directly. Do not paste base64 into chat unless the user explicitly asks.

## Parameter Notes

- `quality`: `low`, `medium`, or `high`.
- `n`: 1 to 10 images.
- `output_format`: `png` or `jpeg` for this skill.
- `gpt-image-2` supports arbitrary resolutions subject to multiples-of-16, long-edge, aspect-ratio, and pixel-count constraints.
