"""Example application using Cobruh."""

import cobruh
from cobruh import DictConfig


@cobruh.main(config_path="configs", config_name="config")
def train(cfg: DictConfig) -> None:
    """Train a model with the provided configuration.
    
    Args:
        cfg: Configuration object containing training parameters.
    """
    print("=" * 60)
    print("Training Configuration")
    print("=" * 60)
    print(f"Model: {cfg.model.name} with {cfg.model.layers} layers")
    print(f"Optimizer: {cfg.optimizer.name}")
    print(f"Learning Rate: {cfg.optimizer.lr}")
    print(f"Batch Size: {cfg.batch_size}")
    print("=" * 60)
    
    # Simulate training
    print("\nStarting training...")
    print(f"Using {cfg.model.name} model")
    print("Training complete!")


if __name__ == "__main__":
    train()
