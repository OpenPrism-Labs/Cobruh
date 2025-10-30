"""Test configuration files."""

import pytest
from cobruh import DictConfig, compose, initialize


@pytest.fixture(scope="package")
def cfg_train_global() -> DictConfig:
    """A pytest fixture for setting up a default Cobruh DictConfig for training.

    :return: A DictConfig object containing a default Cobruh configuration for training.
    """
    with initialize(config_path="../configs"):
        cfg = compose(config_name="train")

        # set defaults for all tests
        cfg.trainer.max_epochs = 1
        cfg.trainer.limit_train_batches = 0.01
        cfg.trainer.limit_val_batches = 0.1
        cfg.trainer.limit_test_batches = 0.1
        cfg.trainer.accelerator = "cpu"
        cfg.trainer.devices = 1
        cfg.data.num_workers = 0
        cfg.data.pin_memory = False
        cfg.extras.print_config = False
        cfg.extras.enforce_tags = False
        cfg.logger = None

    return cfg


@pytest.fixture(scope="package")
def cfg_eval_global() -> DictConfig:
    """A pytest fixture for setting up a default Cobruh DictConfig for evaluation.

    :return: A DictConfig containing a default Cobruh configuration for evaluation.
    """
    with initialize(config_path="../configs"):
        cfg = compose(config_name="eval", overrides=["ckpt_path=."])

        # set defaults for all tests
        cfg.trainer.max_epochs = 1
        cfg.trainer.limit_test_batches = 0.1
        cfg.trainer.accelerator = "cpu"
        cfg.trainer.devices = 1
        cfg.data.num_workers = 0
        cfg.data.pin_memory = False
        cfg.extras.print_config = False
        cfg.extras.enforce_tags = False
        cfg.logger = None

    return cfg


@pytest.fixture(scope="function")
def cfg_train(cfg_train_global: DictConfig, tmp_path) -> DictConfig:
    """A pytest fixture built on top of the `cfg_train_global()` fixture.

    :param cfg_train_global: The input DictConfig object to be modified.
    :param tmp_path: The temporary logging path.

    :return: A DictConfig with updated output and log directories.
    """
    cfg = cfg_train_global.copy()

    cfg.paths.output_dir = str(tmp_path)
    cfg.paths.log_dir = str(tmp_path)

    return cfg


@pytest.fixture(scope="function")
def cfg_eval(cfg_eval_global: DictConfig, tmp_path) -> DictConfig:
    """A pytest fixture built on top of the `cfg_eval_global()` fixture.

    :param cfg_eval_global: The input DictConfig object to be modified.
    :param tmp_path: The temporary logging path.

    :return: A DictConfig with updated output and log directories.
    """
    cfg = cfg_eval_global.copy()

    cfg.paths.output_dir = str(tmp_path)
    cfg.paths.log_dir = str(tmp_path)

    return cfg
