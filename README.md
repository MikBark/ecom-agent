# ecom-agent

## Agent server

It runs a staged Schema-Guided-Reasoning workflow against the request's Playground runtime and streams stages, tool activity, schemas, and the final answer.

## Docker

```shell
docker run -d --rm --name ecom-agent -p 50051:50051 --env-file .env mikbark/ecom-agent
```

## Langfuse observability

Langfuse export is disabled by default. Select one capture level with
`ECOM_AGENT_OBSERVABILITY_MODE`:

- `off`: no Langfuse client is created and no credentials are required.
- `metadata`: exports traces, stages, tool names, timings, outcomes, error categories,
  model information, and token usage without prompts or application payloads.
- `full`: additionally exports prompts, model outputs, tool requests and responses,
  emitted schemas, and final answers. Use this only where the data handling policy
  permits it.

In Langfuse, use the curated Cost and Latency dashboards or create widgets for:

- run volume and outcome;
- run and stage latency;
- input, output, cached-input, and reasoning-output tokens by model or stage;
- model cost;
- tool frequency, latency, and failures.
