"""General utility functions."""

import warnings
from importlib.util import find_spec
from typing import Any, Callable, Dict, Optional, Tuple

from cobruh import DictConfig
from lightning.pytorch.utilities import rank_zero_only

from src.utils import pylogger, rich_utils

log = pylogger.RankedLogger(__name__, rank_zero_only=True)


def extras(cfg: DictConfig) -> None:
    """Apply optional utilities before the training begins.

    Utilities:
        - Ignoring python warnings
        - Rich config printing
        - Enforcing tags from command line
    """
    # disable python warnings
    if cfg.get("extras") and cfg.extras.get("ignore_warnings"):
        log.info("Disabling python warnings! <cfg.extras.ignore_warnings=True>")
        warnings.filterwarnings("ignore")

    # pretty print config tree using Rich library
    if cfg.get("extras") and cfg.extras.get("print_config"):
        log.info("Printing config tree with Rich! <cfg.extras.print_config=True>")
        rich_utils.print_config_tree(cfg, resolve=True, save_to_file=True)

    # enforce tags from command line
    if cfg.get("extras") and cfg.extras.get("enforce_tags"):
        log.info("Enforcing tags! <cfg.extras.enforce_tags=True>")
        rich_utils.enforce_tags(cfg, save_to_file=True)


def task_wrapper(task_func: Callable) -> Callable:
    """Optional decorator that controls the failure behavior when executing the task function.

    This wrapper can be used to:
        - make sure loggers are closed even if the task function raises an exception
        - save the exception to a file
        - mark the run as failed with a dedicated file in the output directory

    :param task_func: The task function to be wrapped.

    :return: The wrapped task function.
    """

    def wrap(cfg: DictConfig) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        try:
            metric_dict, object_dict = task_func(cfg=cfg)

        except Exception as ex:
            log.exception("")  # save exception to `.log` file
            raise ex

        finally:
            # always close loggers
            log.info("Closing loggers...")
            if cfg.get("logger"):
                for lg in cfg.get("logger", []):
                    if hasattr(lg, "experiment") and hasattr(lg.experiment, "finish"):
                        lg.experiment.finish()

        return metric_dict, object_dict

    return wrap


def get_metric_value(metric_dict: Dict[str, Any], metric_name: Optional[str]) -> Optional[float]:
    """Safely retrieves value of the metric logged in LightningModule.

    :param metric_dict: A dict containing metric values.
    :param metric_name: If provided, the name of the metric to retrieve.
    :return: If a metric name was provided, the value of the metric.
    """
    if not metric_name:
        log.info("Metric name is None! Skipping metric value retrieval...")
        return None

    if metric_name not in metric_dict:
        raise ValueError(
            f"Metric value not found! <metric_name={metric_name}>\n"
            "Make sure metric name logged in LightningModule is correct!\n"
            "Make sure `optimized_metric` name in `cobruh_search` config is correct!"
        )

    metric_value = metric_dict[metric_name].item()
    log.info(f"Retrieved metric value! <{metric_name}={metric_value}>")

    return metric_value
