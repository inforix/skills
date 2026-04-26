---
name: imagegen
description: Generate images with Azure OpenAI GPT-image models, especially gpt-image-2 on Azure AI Foundry. Use this skill when the user asks to generate, create, render, or save an image from a text prompt using imagegen, GPT-image, gpt-image-2, Azure OpenAI image generation, or the configured Azure AI Foundry endpoint.
---

# imagegen

Generate images through the Azure OpenAI-compatible image generation API and save the returned base64 image data to local files.

## Defaults

- Endpoint/base URL: `AZURE_OPENAI_BASE_URL`, or `https://maritimeai-resource.openai.azure.com/openai/v1/` if unset.
- API key: `AZURE_OPENAI_API_KEY` is required.
- Model/deployment: `AZURE_OPENAI_IMAGE_MODEL`, or `gpt-image-2` if unset.
- API version header: `AZURE_OPENAI_API_VERSION`, or `preview` if unset.
- Output directory: `./generated-images/` if the user does not specify a file path.

Never write API keys into files, command examples, logs, or final responses.

## Standard Workflow

1. Collect the prompt. If the prompt is missing, ask for it.
2. Choose output settings. Default to `1024x1024`, `high`, `png`, and `n=1` unless the user specifies otherwise.
3. Run the Node CLI from the skills workspace or with an absolute script path:

```bash
node imagegen/scripts/generate-image.mjs \
  --prompt "A watercolor painting of a maritime research vessel at sunrise" \
  --output ./generated-images/ship.png
```

4. Report the saved file path(s), model, size, quality, and format.
5. If Azure returns an error, preserve the status code and message, but redact secrets.

## Command Reference

```bash
node imagegen/scripts/generate-image.mjs \
  --prompt "A cinematic harbor at dawn" \
  --size 1536x1024 \
  --quality high \
  --format png \
  --n 1 \
  --output ./generated-images/harbor.png
```

Optional environment overrides:

```bash
export AZURE_OPENAI_BASE_URL="https://maritimeai-resource.openai.azure.com/openai/v1/"
export AZURE_OPENAI_IMAGE_MODEL="gpt-image-2"
export AZURE_OPENAI_API_VERSION="preview"
```

Useful CLI flags:

- `--prompt <text>`: text prompt for image generation.
- `--prompt-file <path>`: read the prompt from a UTF-8 file.
- `--output <path>`: output file path for one image, or filename prefix when `n > 1`.
- `--output-dir <path>`: directory for auto-named outputs.
- `--base-url <url>`: override `AZURE_OPENAI_BASE_URL`.
- `--model <name>`: override `AZURE_OPENAI_IMAGE_MODEL`.
- `--size <WxH>`: image size, such as `1024x1024`.
- `--quality <low|medium|high>`: generation quality.
- `--format <png|jpeg>`: output format.
- `--n <1-10>`: number of images.
- `--user <id>`: optional end-user identifier for Azure/OpenAI tracking.
- `--timeout-ms <ms>`: request timeout, default `180000`.
- `--dry-run`: validate inputs and print the redacted request without calling Azure.

## GPT-image-2 Size Rules

For `gpt-image-2`, validate custom sizes before calling the API:

- Width and height must both be multiples of 16.
- Long edge must be no more than 3840 px.
- Aspect ratio must be no more than 3:1.
- Total pixels must be between 655,360 and 8,294,400.

Use `1024x1024` when unsure.

## Reference

Read `references/azure-openai-image-api.md` when troubleshooting API shape, headers, endpoint variants, or model parameter constraints.
