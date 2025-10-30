"""Tests for training pipeline."""

import os
from pathlib import Path

import pytest
from cobruh import DictConfig

from src.train import train


@pytest.mark.slow
def test_train_fast_dev_run(cfg_train: DictConfig) -> None:
    """Run 1 train, val and test step.

    :param cfg_train: A DictConfig containing a valid training configuration.
    """
    cfg_train.trainer.fast_dev_run = True
    train(cfg_train)


@pytest.mark.slow
def test_train_epoch(tmp_path: Path, cfg_train: DictConfig) -> None:
    """Train for 1 epoch.

    :param tmp_path: The temporary logging path.
    :param cfg_train: A DictConfig containing a valid training configuration.
    """
    cfg_train.trainer.max_epochs = 1
    train(cfg_train)


@pytest.mark.slow
def test_train_resume(tmp_path: Path, cfg_train: DictConfig) -> None:
    """Run 1 epoch, finish, and resume for another epoch.

    :param tmp_path: The temporary logging path.
    :param cfg_train: A DictConfig containing a valid training configuration.
    """
    cfg_train.trainer.max_epochs = 1
    metric_dict_1, _ = train(cfg_train)

    files = os.listdir(tmp_path / "checkpoints")
    assert "last.ckpt" in files

    cfg_train.ckpt_path = str(tmp_path / "checkpoints" / "last.ckpt")
    cfg_train.trainer.max_epochs = 2

    metric_dict_2, _ = train(cfg_train)
