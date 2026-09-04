"""Compose and display the maintained Cobruh example configuration."""

from __future__ import annotations

import sys

from cobruh import Cobruh


def main() -> None:
    project = Cobruh("examples/configs", project_root=".")
    config = project.compose("config", overrides=sys.argv[1:])

    print(f"Model: {config['model']['name']} ({config['model']['layers']} layers)")
    print(f"Optimizer: {config['optimizer']['name']}")
    print(f"Learning rate: {config['optimizer']['lr']}")
    print(f"Batch size: {config['batch_size']}")


if __name__ == "__main__":
    main()
