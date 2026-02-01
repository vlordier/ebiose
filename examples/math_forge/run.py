"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

import asyncio
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from ebiose.core.forge_cycle import CloudForgeCycleConfig
from examples.math_forge.math_forge import MathLangGraphForge


@dataclass
class RunConfig:
    """Configuration for run."""

    train_csv_path: str
    test_csv_path: str
    save_path: Path
    n_problems: int
    budget: float
    default_model_endpoint_id: str | None = None
    mode: Literal["cloud", "local"] = "cloud"


def main(config: RunConfig) -> None:
    forge = MathLangGraphForge(
        train_csv_path=config.train_csv_path,
        test_csv_path=config.test_csv_path,
        n_problems=config.n_problems,
        default_model_endpoint_id=config.default_model_endpoint_id,
    )

    cycle_config = None
    if config.mode == "cloud":
        cycle_config = CloudForgeCycleConfig(
            budget=config.budget,
            n_agents_in_population=2,
            n_selected_agents_from_ecosystem=1,
            n_best_agents_to_return=2,
            replacement_ratio=0.5,
            local_results_path=config.save_path,
        )
    else:
        sys.exit("Running in local mode is not fully implemented yet.")

    best_agents, best_finess = asyncio.run(
        forge.run_new_cycle(config=cycle_config),
    )

    forge.display_results(best_agents, best_finess)


if __name__ == "__main__":
    # loading dotenv
    from dotenv import load_dotenv

    load_dotenv()

    # the path where results will be saved
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d_%H-%M-%S")
    SAVE_PATH = Path(f"./data/{timestamp}/")
    if not SAVE_PATH.exists():
        SAVE_PATH.mkdir(parents=True)

    # run parameters
    BUDGET = 0.025  # budget in dollars
    N_PROBLEMS = 2  # number of problems to evaluate on, per generation
    TRAIN_CSV_PATH = "./examples/math_forge/gsm8k_train.csv"  # the train dataset
    TEST_CSV_PATH = "./examples/math_forge/gsm8k_test.csv"  # the test dataset
    DEFAULT_MODEL_ENDPOINT_ID = (
        None  # set if you want to use a specific model endpoint for generated agents
    )

    # running the forge cycle
    config = RunConfig(
        train_csv_path=TRAIN_CSV_PATH,
        test_csv_path=TEST_CSV_PATH,
        n_problems=N_PROBLEMS,
        budget=BUDGET,
        save_path=SAVE_PATH,
        default_model_endpoint_id=DEFAULT_MODEL_ENDPOINT_ID,
        mode="cloud",
    )
    main(config)
