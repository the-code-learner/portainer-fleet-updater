# Architecture

Portainer Fleet Updater is designed as a small control-plane companion for Portainer.

## Principles

- Portainer remains the inventory of environments and stacks.
- No second host list, SSH inventory or Ansible controller is required.
- The public repository never contains deployment secrets.
- The Portainer API token is supplied only in the operator's private stack configuration.
- Destructive operations are explicit and reviewable.
- Server and Agent upgrades will be version-synchronized.
- Remote Agent upgrades will eventually use short-lived workers created through the Portainer Docker proxy.
- Stack management uses automatic discovery and persistent operator-selected checkboxes.

## Deployment lifecycle

The deployment system intentionally follows the same model used by Postmaster MCP:

1. The Portainer YAML is only a bootstrap layer.
2. Application code lives in normal repository files.
3. `PFU_VERSION=latest` resolves only stable `vX.Y.Z` GitHub Releases.
4. Explicit versions remain pinned.
5. Releases are downloaded into staging, validated and activated atomically.
6. The previous known-good release stays cached.
7. Temporary GitHub/network failures may fall back to the cached current release.
8. Persistent source cache, Python virtual environment and application data use separate volumes.

## v0.1.0 safety boundary

v0.1.0 performs discovery and local preference writes only. It does not pull images, recreate Portainer, recreate Agents or redeploy stacks.

The Docker socket is highly privileged even when mounted with `:ro`; the `:ro` mount flag does not make the Docker API read-only. Do not expose the UI publicly.
