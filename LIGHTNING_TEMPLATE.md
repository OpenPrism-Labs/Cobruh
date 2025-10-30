# Lightning-Cobruh Template

A comprehensive PyTorch Lightning project template using Cobruh for configuration management, inspired by the popular [lightning-hydra-template](https://github.com/ashleve/lightning-hydra-template).

## 📍 Location

This template is located in the `lightning-cobruh-template/` directory within the Cobruh repository.

## 🎯 Purpose

Provides a production-ready template for deep learning projects that combines:
- **PyTorch Lightning** for training infrastructure
- **Cobruh** for configuration management
- **Best Practices** from the ML community

## ✨ Features

- ✅ Hierarchical configuration management with Cobruh
- ✅ Complete PyTorch Lightning integration
- ✅ Working MNIST example out of the box
- ✅ Modular architecture (data, models, utils)
- ✅ Command-line overrides for all parameters
- ✅ Experiment tracking with multiple loggers
- ✅ Comprehensive test suite with pytest
- ✅ GPU/CPU training support
- ✅ Debug modes for rapid development
- ✅ Checkpoint management
- ✅ Well-documented code and configs

## 🚀 Quick Start

```bash
# Navigate to the template directory
cd lightning-cobruh-template

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Run training with MNIST example
python src/train.py

# Or with GPU
python src/train.py trainer=gpu

# Or with custom parameters
python src/train.py trainer.max_epochs=20 data.batch_size=64
```

## 📚 Documentation

See the template directory for comprehensive documentation:

- **README.md** - Overview and features
- **GETTING_STARTED.md** - Step-by-step guide
- **EXAMPLES.md** - Usage examples
- **IMPLEMENTATION_SUMMARY.md** - Implementation details

## 🏗️ Project Structure

```
lightning-cobruh-template/
├── configs/              # All configuration files
│   ├── callbacks/       # Callback configurations
│   ├── data/           # Data configurations
│   ├── debug/          # Debug mode configs
│   ├── experiment/     # Experiment configs
│   ├── logger/         # Logger configurations
│   ├── model/          # Model configurations
│   ├── trainer/        # Trainer configurations
│   ├── train.yaml      # Main training config
│   └── eval.yaml       # Main evaluation config
│
├── src/                 # Source code
│   ├── data/           # Data modules
│   ├── models/         # Model implementations
│   ├── utils/          # Utility functions
│   ├── train.py        # Training script
│   └── eval.py         # Evaluation script
│
├── tests/              # Test suite
│   └── unit/          # Unit tests
│
└── docs/              # Documentation
```

## 💡 Usage Examples

### Basic Training
```bash
python src/train.py
```

### Use Experiment Config
```bash
python src/train.py experiment=example
```

### Override Parameters
```bash
python src/train.py \
    trainer.max_epochs=50 \
    data.batch_size=128 \
    model.optimizer.lr=0.001
```

### Debug Mode (Fast Dev Run)
```bash
python src/train.py debug=fdr
```

### GPU Training with Mixed Precision
```bash
python src/train.py trainer=gpu trainer.precision=16-mixed
```

### Enable Logging
```bash
python src/train.py logger=tensorboard
```

## 🔧 Customization

### Add Your Own Data

1. Create a LightningDataModule in `src/data/`
2. Create a config file in `configs/data/`
3. Run: `python src/train.py data=your_data`

### Add Your Own Model

1. Create a LightningModule in `src/models/`
2. Create a config file in `configs/model/`
3. Run: `python src/train.py model=your_model`

### Create Experiments

1. Create experiment config in `configs/experiment/`
2. Run: `python src/train.py experiment=your_experiment`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/unit/test_train.py

# Run with coverage
pytest --cov=src

# Run only fast tests
pytest -k "not slow"
```

## 📋 Requirements

- Python 3.10+
- PyTorch 2.0+
- PyTorch Lightning 2.0+
- Cobruh
- Rich (for pretty printing)

See `requirements.txt` for complete list.

## 🎓 Learning Resources

- [PyTorch Lightning Docs](https://lightning.ai/docs/pytorch/)
- [Cobruh Documentation](https://github.com/OpenPrism-Labs/Cobruh)
- [Template Getting Started Guide](./lightning-cobruh-template/GETTING_STARTED.md)

## 🤝 Comparison with Hydra Template

| Feature | Lightning-Hydra | Lightning-Cobruh |
|---------|----------------|------------------|
| Config System | Hydra | Cobruh |
| Python Version | 3.8+ | 3.10+ |
| Complexity | Higher | Lower |
| Learning Curve | Steeper | Gentler |
| IDE Support | Good | Excellent |
| Type Hints | Partial | Full |
| Performance | Fast | Fast |

## 📝 License

MIT License - See LICENSE file in the template directory.

## 🙏 Acknowledgments

- Inspired by [lightning-hydra-template](https://github.com/ashleve/lightning-hydra-template)
- Built with [PyTorch Lightning](https://github.com/Lightning-AI/lightning)
- Configuration management with [Cobruh](https://github.com/OpenPrism-Labs/Cobruh)

## 💬 Support

For questions and issues:
- Open an issue in the Cobruh repository
- Check the template documentation
- Review the example configurations

---

**Happy Training! 🚀⚡**
