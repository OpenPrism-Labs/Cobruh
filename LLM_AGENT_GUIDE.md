# LLM Coding Agent Guide: Building Cobruh

> **Quick Start Guide for AI Coding Agents**  
> Last Updated: October 25, 2025 | Version: 1.0.0

---

## 🎯 Mission

Build **Cobruh** - a hierarchical configuration management framework for Python applications, inspired by Facebook's Hydra. Enable composable, type-safe configuration with YAML support, command-line overrides, and structured configs.

---

## 📚 Complete Documentation

**All detailed documentation is in the `llm_docs/` directory:**

- 📖 **[llm_docs/README_AGENT.md](llm_docs/README_AGENT.md)** - Navigation hub and documentation guide
- 🏗️ **[llm_docs/architecture/ARCHITECTURE.md](llm_docs/architecture/ARCHITECTURE.md)** - System design and algorithms
- 📦 **[llm_docs/architecture/PROJECT_STRUCTURE.md](llm_docs/architecture/PROJECT_STRUCTURE.md)** - File organization
- 🛤️ **[llm_docs/implementation/IMPLEMENTATION_ROADMAP.md](llm_docs/implementation/IMPLEMENTATION_ROADMAP.md)** - 12-week development plan
- 🔌 **[llm_docs/api/API_SPECIFICATION.md](llm_docs/api/API_SPECIFICATION.md)** - Complete API reference
- ✅ **[llm_docs/testing/TESTING_STRATEGY.md](llm_docs/testing/TESTING_STRATEGY.md)** - Testing approach

---

## ⚡ Quick Reference

### What You're Building

A Python library that enables developers to:

1. **Manage configurations hierarchically** - Split configs into reusable groups
2. **Compose dynamically** - Merge multiple configs with overrides
3. **Type-safe configs** - Validate using Python dataclasses
4. **Command-line overrides** - Override any config value from CLI
5. **Interpolation** - Reference config values and environment variables
6. **Instantiate objects** - Create Python objects from config

### Example Usage

```yaml
# config.yaml
defaults:
  - model: resnet50
  - optimizer: adam

batch_size: 32
learning_rate: ${optimizer.lr}  # Interpolation
```

```python
"""app.py - Training application with Cobruh configuration."""
import cobruh
from cobruh import DictConfig


@cobruh.main(config_path="configs", config_name="config")
def train(cfg: DictConfig):
    """Train a model with the provided configuration.
    
    Args:
        cfg: Configuration object containing training parameters.
    """
    print(f"Batch size: {cfg.batch_size}")
    model = cobruh.utils.instantiate(cfg.model)


if __name__ == "__main__":
    train()
```

```bash
# CLI usage
python app.py model=vgg optimizer=sgd batch_size=64
```

---

## 🚀 Getting Started (5 Steps)

### Step 1: Read the Architecture
Start with **[llm_docs/architecture/ARCHITECTURE.md](llm_docs/architecture/ARCHITECTURE.md)** to understand:
- Core design principles
- System architecture
- Key algorithms (composition, merging, interpolation)

### Step 2: Understand Project Structure
Read **[llm_docs/architecture/PROJECT_STRUCTURE.md](llm_docs/architecture/PROJECT_STRUCTURE.md)** to see:
- Directory layout
- Module responsibilities
- Import structure

### Step 3: Follow the Roadmap
Use **[llm_docs/implementation/IMPLEMENTATION_ROADMAP.md](llm_docs/implementation/IMPLEMENTATION_ROADMAP.md)** for:
- 12-week development plan (4 phases)
- Specific milestones and tasks
- Acceptance criteria for each phase

### Step 4: Implement the API
Reference **[llm_docs/api/API_SPECIFICATION.md](llm_docs/api/API_SPECIFICATION.md)** for:
- Public API design
- Usage examples
- Type signatures

### Step 5: Test Everything
Follow **[llm_docs/testing/TESTING_STRATEGY.md](llm_docs/testing/TESTING_STRATEGY.md)** to:
- Write comprehensive tests
- Achieve >90% coverage
- Ensure quality

---

## 📋 Implementation Checklist

### Critical Path (Must Have for v1.0)

1. ✅ **DictConfig/ListConfig** - Core data structures
2. ✅ **YAML Loader** - Load configurations
3. ✅ **Config Merger** - Merge multiple configs
4. ✅ **Override Parser** - Parse CLI overrides
5. ✅ **Override Applier** - Apply overrides to config
6. ✅ **Interpolation** - Basic `${key}` resolution
7. ✅ **Composer** - Orchestrate composition
8. ✅ **Main Decorator** - `@cobruh.main()`
9. ✅ **Instantiate** - `cobruh.utils.instantiate()`
10. ✅ **Tests** - Core functionality tests

### Important (Should Have for v1.0)

1. ✅ **Structured Configs** - Dataclass support
2. ✅ **ConfigStore** - Config registry
3. ✅ **Environment Resolvers** - `${env:VAR}`
4. ✅ **Defaults List** - Process defaults
5. ✅ **Error Messages** - Clear, helpful errors
6. ✅ **Type Validation** - Runtime type checking

### Nice to Have (Can Defer to v1.1)

1. ⏸️ **Multirun** - Parameter sweeps
2. ⏸️ **Plugins** - Extension system
3. ⏸️ **Tab Completion** - Shell completion
4. ⏸️ **Schema Generation** - Auto-generate schemas

---

## 💡 Quick Tips for LLM Agents

### Development Approach

1. **Start Small**: Begin with core containers (DictConfig, ListConfig)
2. **Test Early**: Write tests as you implement each component
3. **Reference Often**: Use the detailed docs for implementation specifics
4. **Follow the Plan**: The roadmap builds features incrementally
5. **Incremental**: Make small, testable changes

### Code Style Guidelines

**Follow PEP 8 conventions strictly:**

- **PEP 8**: Style Guide for Python Code
  - Use 4 spaces for indentation (never tabs)
  - Maximum line length of 79 characters for code, 72 for docstrings
  - Use lowercase with underscores for function and variable names (e.g., `dict_config`, `merge_configs`)
  - Use lowercase for module names (e.g., `cobruh`, `config_loader`)
  - Use PascalCase for class names (e.g., `DictConfig`, `ConfigStore`)
  - Two blank lines before top-level function/class definitions
  - One blank line between methods in a class
  - Organize imports: standard library → third-party → local modules

- **PEP 257**: Docstring Conventions
  - Add docstrings to all modules, classes, and public functions
  - Use triple double-quotes `"""`
  - First line should be a concise summary
  - Include Args, Returns, Raises sections for functions

- **PEP 484**: Type Hints
  - Use type hints for all function parameters and return values
  - Example: `def merge(base: DictConfig, override: DictConfig) -> DictConfig:`

- **Additional Standards**:
  - Use `pylint` or `ruff` for linting
  - Use `black` for automatic code formatting
  - Use `mypy` for static type checking
  - Aim for >90% test coverage

### Key Points

- **All algorithms** are documented in [architecture/ARCHITECTURE.md](llm_docs/architecture/ARCHITECTURE.md)
- **All phases/milestones** are in [implementation/IMPLEMENTATION_ROADMAP.md](llm_docs/implementation/IMPLEMENTATION_ROADMAP.md)
- **All API details** are in [api/API_SPECIFICATION.md](llm_docs/api/API_SPECIFICATION.md)
- **All testing patterns** are in [testing/TESTING_STRATEGY.md](llm_docs/testing/TESTING_STRATEGY.md)

### Common Questions

**Q: Where do I start?**  
A: Read ARCHITECTURE.md, then start Phase 1 from IMPLEMENTATION_ROADMAP.md

**Q: How do I implement X?**  
A: Check ARCHITECTURE.md for algorithms, API_SPECIFICATION.md for examples

**Q: What should I test?**  
A: Follow TESTING_STRATEGY.md for comprehensive test coverage

**Q: What files do I create?**  
A: See PROJECT_STRUCTURE.md for complete directory layout

---

## 📦 Final Deliverables

Before calling it v1.0:

- [ ] All core features implemented (see checklist above)
- [ ] >90% test coverage
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Examples working
- [ ] PyPI package built
- [ ] CI/CD pipeline working
- [ ] README.md complete
- [ ] LICENSE file included
- [ ] CHANGELOG.md started

---

## 🔗 External Resources

### Inspiration Projects

- **Facebook Hydra**: https://github.com/facebookresearch/hydra
- **OmegaConf**: https://github.com/omry/omegaconf
- **PyYAML**: https://pyyaml.org/

### Python Packaging

- **PyPI**: https://pypi.org/
- **setuptools**: https://setuptools.pypa.io/
- **pytest**: https://pytest.org/

---

## 🚀 Let's Build!

You have everything you need to build Cobruh:

- ✅ Clear mission and goals
- ✅ Comprehensive documentation in `llm_docs/`
- ✅ Step-by-step roadmap
- ✅ API specifications
- ✅ Testing strategy
- ✅ Project structure

**Start with Step 1 above and follow the roadmap. Good luck!** 🎉

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0  
**Status**: Ready for implementation
