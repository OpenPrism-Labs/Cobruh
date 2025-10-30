# Lightning-Cobruh Template - Examples

This directory contains example scripts and notebooks to help you get started.

## Examples

### 1. Simple Training Script

See `src/train.py` for the main training script.

Basic usage:
```bash
python src/train.py
```

### 2. Custom Experiment

Create your own experiment config in `configs/experiment/` and run:
```bash
python src/train.py experiment=my_experiment
```

### 3. Using Different Loggers

Train with TensorBoard:
```bash
python src/train.py logger=tensorboard
```

Train with CSV logger:
```bash
python src/train.py logger=csv
```

### 4. Hyperparameter Tuning

Override hyperparameters from command line:
```bash
python src/train.py \
    model.optimizer.lr=0.001,0.0001,0.00001 \
    data.batch_size=32,64,128
```

### 5. Multi-GPU Training

Train on multiple GPUs:
```bash
python src/train.py trainer=gpu trainer.devices=2 trainer.strategy=ddp
```

## Notebooks

- `explore_template.md` - Interactive exploration of the template
- Add your own notebooks here!

## Scripts

See the `scripts/` directory for example shell scripts:
- `schedule.sh` - Run multiple training jobs sequentially

## Creating Your Own Examples

1. Create a new experiment config in `configs/experiment/`
2. Add custom data modules in `src/data/`
3. Add custom models in `src/models/`
4. Run with: `python src/train.py experiment=your_experiment`
