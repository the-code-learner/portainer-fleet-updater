# Portainer Fleet Updater

A small self-hosted companion for Portainer that aims to make Portainer Server, Portainer Agents and selected Docker stacks easier to review and update from one place.

> **Status:** v0.1.0 is a safe discovery baseline. It does not update Portainer, Agents or stacks yet.

## Why

Portainer simplifies application deployment, but Portainer Server and classic Agents still need their own maintenance. Fleet Updater is intended to use Portainer itself as the inventory:

- discover the local Portainer Server;
- discover all environments already registered in Portainer;
- discover all Portainer-managed stacks;
- let the operator select managed stacks with checkboxes;
- later, synchronize Server/Agent versions and perform controlled stack pull/redeploy operations.

No manual host inventory, SSH key list or Ansible controller is required.

## Public repository / secrets

This repository is public. **Never commit API tokens, passwords, environment-specific URLs or other secrets.**

Create a Portainer API access token and place it only in your private Portainer Stack environment:

```yaml
PORTAINER_API_TOKEN: "ptr_..."
```

The token is intentionally empty in the committed deployment YAML.

## Single-YAML Portainer deployment

Deployment follows the same versioned single-YAML pattern used by Postmaster MCP.

1. Open **Portainer → Stacks → Add stack**.
2. Copy `portainer-fleet-updater.yml`.
3. Set `PORTAINER_API_TOKEN` in your private stack.
4. Deploy.
5. By default the dashboard is published only on `127.0.0.1:9080`.

For a remote browser, use an SSH tunnel:

```bash
ssh -L 9080:127.0.0.1:9080 root@YOUR_DOCKER_HOST
```

Then open `http://127.0.0.1:9080`.

If you intentionally want LAN exposure, change the port binding in your private stack.

## Version and update model

The bootstrap is deliberately independent from a custom Docker image:

- base runtime: `python:3.12-slim-bookworm`;
- `PFU_VERSION=latest` means the highest stable GitHub Release matching `vX.Y.Z`;
- `main`, drafts and prereleases are never treated as `latest`;
- an explicit version/tag remains pinned;
- source is downloaded to a staging release directory;
- activation switches `current` only after validation;
- the previous known-good release remains cached;
- source cache, Python venv and application data use separate persistent volumes.

## Current v0.1.0 features

- automatic local Portainer container discovery through the Docker socket;
- optional explicit `PORTAINER_URL` override;
- Portainer Server version/status;
- environment discovery;
- reported Agent versions;
- stack discovery across environments;
- persistent managed-stack checkbox selection under `/data/settings.json`;
- health endpoint at `/healthz`;
- no destructive Portainer calls.

## Security

The Docker socket is equivalent to highly privileged host access. Mounting it with `:ro` does **not** make the Docker API read-only.

For that reason:

- do not expose Fleet Updater directly to the Internet;
- use a dedicated Portainer API token;
- keep secrets only in private deployment configuration;
- v0.1.0 performs only Docker/Portainer GET operations plus writes to its own `/data` volume.

## Roadmap

- image/update status for selected stacks;
- pull & redeploy selected stacks with explicit confirmation;
- Portainer Server controlled update;
- classic Agent synchronized update via short-lived remote workers;
- health verification and rollback;
- self-update preview/execute flow using the same release lifecycle as Postmaster MCP.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
