"""Minimal health check for container hosts. Exits 0 if the process is alive."""
import os
import sys

# The bot process itself is the liveness signal; a running container with this
# script executed means the entrypoint hasn't crashed. We simply verify we can
# import the package (catches broken installs) and report healthy.
try:
    import rosy  # noqa: F401
except Exception as exc:  # noqa: BLE001
    print(f"healthcheck failed: {exc}", file=sys.stderr)
    sys.exit(1)

sys.exit(0)
