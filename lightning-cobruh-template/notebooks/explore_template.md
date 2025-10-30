# Simple notebook for exploring the template

This notebook can be used to explore the Lightning-Cobruh template interactively.

## Setup

```python
import sys
sys.path.append('..')

from cobruh import compose, initialize
from cobruh.utils import instantiate
import torch
```

## Load Configuration

```python
# Initialize and compose configuration
with initialize(config_path="../configs"):
    cfg = compose(config_name="train")

print(cfg)
```

## Instantiate Components

```python
# Instantiate data module
datamodule = instantiate(cfg.data)
datamodule.prepare_data()
datamodule.setup("fit")

# Instantiate model
model = instantiate(cfg.model)

print(f"Model: {model}")
print(f"DataModule: {datamodule}")
```

## Explore Data

```python
# Get a batch of data
train_loader = datamodule.train_dataloader()
batch = next(iter(train_loader))
x, y = batch

print(f"Batch shape: {x.shape}")
print(f"Labels shape: {y.shape}")
print(f"Sample labels: {y[:10]}")
```

## Test Forward Pass

```python
# Test model forward pass
with torch.no_grad():
    logits = model(x)
    print(f"Output shape: {logits.shape}")
    predictions = torch.argmax(logits, dim=1)
    print(f"Predictions: {predictions[:10]}")
```

## Visualize Samples

```python
import matplotlib.pyplot as plt

# Visualize some samples
fig, axes = plt.subplots(2, 5, figsize=(12, 5))
for i, ax in enumerate(axes.flat):
    img = x[i].squeeze()
    ax.imshow(img, cmap='gray')
    ax.set_title(f"Label: {y[i]}")
    ax.axis('off')
plt.tight_layout()
plt.show()
```
