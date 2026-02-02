"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

import asyncio
import csv
import random
from pathlib import Path
from typing import Literal, Self, cast

from pydantic import BaseModel, Field, model_validator

from ebiose.core.agent import Agent
from ebiose.core.agent_forge import AgentForge


class AgentInput(BaseModel):
    math_problem: str


class AgentOutput(BaseModel):
    solution: int
    rationale: str


class MathLangGraphForge(AgentForge):
    name: str = "MathLangGraphForge"
    description: str = "Solving word math problems"
    train_csv_path: str
    test_csv_path: str
    n_problems: int | None = None

    agent_input_model: type[BaseModel] = AgentInput
    agent_output_model: type[BaseModel] = AgentOutput
    default_generated_agent_engine_type: str = "langgraph_engine"

    data: dict[str, dict] = Field(default_factory=dict, exclude=True)
    fitness: dict[str, dict[str, float]] = Field(default_factory=dict, exclude=True)
    current_generation: int = Field(default=0, exclude=True)
    current_problem_ids: list[str] = Field(default_factory=list, exclude=True)

    unpicked_problems: dict[str, list[str]] = Field(default_factory=dict, exclude=True)

    @model_validator(mode="after")
    def _load_data(self) -> Self:
        for name, path in zip(
            ["train", "test"],
            [self.train_csv_path, self.test_csv_path],
            strict=True,
        ):
            with Path(path).open("r") as csvfile:
                reader = csv.DictReader(csvfile)
                self.data[name] = {
                    row["problem_id"]: {
                        "problem": row["problem"],
                        "solution": int(row["solution"]),
                    }
                    for row in reader
                }
        return self

    def pick_problems(self, mode: Literal["train", "test"] = "test") -> list[str]:
        # When no specific number is set, return all problems
        if self.n_problems is None:
            return list(self.data[mode].keys())

        if (
            mode not in self.unpicked_problems
            or len(self.unpicked_problems[mode]) < self.n_problems
        ):
            # Reset the pool when there aren't enough problems left
            self.unpicked_problems[mode] = list(self.data[mode].keys())
            random.shuffle(self.unpicked_problems[mode])

        # Select and remove n_problems from the pool
        selected = self.unpicked_problems[mode][: self.n_problems]
        self.unpicked_problems[mode] = self.unpicked_problems[mode][self.n_problems :]
        return selected

    async def _evaluate_problem(
        self,
        agent: Agent,
        problem_id: str,
        mode: Literal["train", "test"],
        forge_cycle_id: str | None,
        **kwargs: object,
    ) -> float | AgentOutput:
        """Evaluate a single problem for an agent."""
        # Use cached fitness if available
        if agent.id in self.fitness and problem_id in self.fitness[agent.id]:
            await asyncio.sleep(0)
            return float(self.fitness[agent.id][problem_id])

        # Run agent on problem
        agent_input = self.agent_input_model(
            math_problem=self.data[mode][problem_id]["problem"],
        )
        result = await agent.run(
            agent_input,
            master_agent_id=agent.id,
            forge_cycle_id=forge_cycle_id,
            **kwargs,
        )
        return cast("AgentOutput", result)

    def _update_fitness_for_result(
        self,
        agent_id: str,
        problem_id: str,
        result: AgentOutput | float | BaseException,
        mode: Literal["train", "test"],
    ) -> float:
        """Update fitness cache for a single result and return fitness score."""
        if agent_id not in self.fitness:
            self.fitness[agent_id] = {}

        # Handle cached or numeric results
        if isinstance(result, (int, float)):
            return float(result)

        # Handle exceptions
        if isinstance(result, BaseException):
            self.fitness[agent_id][problem_id] = 0
            return 0.0

        # Handle AgentOutput
        if result.solution == self.data[mode][problem_id]["solution"]:
            self.fitness[agent_id][problem_id] = 1
            return 1.0

        self.fitness[agent_id][problem_id] = 0
        return 0.0

    async def compute_fitness(
        self,
        agent: Agent,
        **kwargs: str | float | bool | BaseModel,
    ) -> tuple[str, float]:
        forge_cycle_id = cast("str | None", kwargs.get("forge_cycle_id"))
        mode = cast("Literal['train', 'test']", kwargs.get("mode", "train"))
        agent_engine = agent.agent_engine
        if agent_engine is None or agent_engine.engine_type != "langgraph_engine":
            self.fitness[agent.id] = {}
            return agent.id, 0.0

        # Update problem set if generation changed
        generation_obj = kwargs.get("generation", 0)
        generation = (
            int(generation_obj) if isinstance(generation_obj, (int, float, str)) else 0
        )
        if generation != self.current_generation or (
            self.n_problems is not None
            and len(self.current_problem_ids) != self.n_problems
        ):
            self.current_generation = generation
            self.current_problem_ids = self.pick_problems(mode=mode)

        # Evaluate all problems concurrently
        tasks = [
            self._evaluate_problem(
                agent,
                problem_id,
                mode,
                forge_cycle_id,
                **kwargs,
            )
            for problem_id in self.current_problem_ids
        ]

        results: list[AgentOutput | float | BaseException] = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        # Calculate total fitness
        fitness = sum(
            self._update_fitness_for_result(agent.id, problem_id, result, mode)
            for problem_id, result in zip(
                self.current_problem_ids,
                results,
                strict=True,
            )
        )

        # Normalize fitness score
        total_problems = (
            self.n_problems if self.n_problems is not None else len(self.data[mode])
        )
        return agent.id, fitness / total_problems
