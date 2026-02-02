"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel, SecretStr


class ModelType(Enum):
    """Model type categories."""

    LLM = "LLM"


class ModelSize(Enum):
    """Model size categories used for pricing tiers."""

    SMALL = "Small"  # max 3B - 1M input token 10c
    MEDIUM = "Medium"  # max 15B - 1M input token 50c
    LARGE = "Large"  # max 90B - 1M input token 300c
    EXTRA_LARGE = "Extra Large"  # 90B+ - 1M input token +300c


class ModelEndpoint(BaseModel):
    """Configuration for a single model endpoint."""

    endpoint_id: str
    provider: str

    # model endpoint config
    api_key: SecretStr | None = None
    endpoint_url: SecretStr | None = None
    api_version: str | None = None
    deployment_name: str | None = None


class EbioseAPIConfig(BaseModel):
    """Configuration for Ebiose cloud API access."""

    api_key: SecretStr | None = None
    api_base: str | None = None


# Compute the project root and set the default file path for model_endpoints.yml.
DEFAULT_MODEL_ENDPOINTS_PATH = (
    Path(__file__).resolve().parents[2] / "model_endpoints.yml"
)


class ModelEndpoints:
    """Registry and access helpers for model endpoint configuration."""

    _default_agent_endpoint_id: str | None = None
    _default_meta_agent_endpoint_id: str | None = None
    _default_utility_agent_endpoint_id: str | None = None
    _ebiose_api_config: EbioseAPIConfig | None = None
    _lite_llm: ClassVar[dict[str, Any]] = {"use": False, "use_proxy": False}
    _endpoints: ClassVar[list[ModelEndpoint]] = []

    @staticmethod
    def get_default_model_endpoint_id() -> str:
        """Get the default agent model endpoint ID.

        Returns:
            The default agent endpoint ID.

        Raises:
            ValueError: If default endpoint ID is not set.

        """
        if ModelEndpoints._default_agent_endpoint_id is None:
            ModelEndpoints.load_model_endpoints()
        if ModelEndpoints._default_agent_endpoint_id is None:
            msg = "Default agent endpoint ID is not set"
            raise ValueError(msg)
        return ModelEndpoints._default_agent_endpoint_id

    @staticmethod
    def get_default_meta_agent_endpoint_id() -> str:
        """Get the default meta agent model endpoint ID.

        Returns:
            The default meta agent endpoint ID, or default agent endpoint ID if not set.

        """
        if ModelEndpoints._default_meta_agent_endpoint_id is None:
            ModelEndpoints.load_model_endpoints()
        if ModelEndpoints._default_meta_agent_endpoint_id is None:
            return ModelEndpoints.get_default_model_endpoint_id()
        return ModelEndpoints._default_meta_agent_endpoint_id

    @staticmethod
    def get_default_utility_agent_endpoint_id() -> str:
        """Get the default utility agent model endpoint ID.

        Returns:
            The default utility agent endpoint ID, or default agent endpoint ID if not set.

        """
        if ModelEndpoints._default_utility_agent_endpoint_id is None:
            ModelEndpoints.load_model_endpoints()
        if ModelEndpoints._default_utility_agent_endpoint_id is None:
            return ModelEndpoints.get_default_model_endpoint_id()
        return ModelEndpoints._default_utility_agent_endpoint_id

    @staticmethod
    def get_ebiose_api_key() -> str | None:
        """Get the Ebiose API key from configuration.

        Returns:
            The API key if configured, None otherwise.

        """
        if ModelEndpoints._ebiose_api_config is None:
            ModelEndpoints.load_model_endpoints()
        if (
            ModelEndpoints._ebiose_api_config is not None
            and ModelEndpoints._ebiose_api_config.api_key is not None
        ):
            return ModelEndpoints._ebiose_api_config.api_key.get_secret_value()
        return None

    @staticmethod
    def get_ebiose_api_base() -> str | None:
        """Get the Ebiose API base URL from configuration.

        Returns:
            The API base URL if configured, None otherwise.

        """
        if ModelEndpoints._ebiose_api_config is None:
            ModelEndpoints.load_model_endpoints()
        if ModelEndpoints._ebiose_api_config is not None:
            return ModelEndpoints._ebiose_api_config.api_base
        return None

    @staticmethod
    def use_lite_llm() -> bool:
        """Check if LiteLLM is enabled.

        Returns:
            True if LiteLLM is enabled, False otherwise.

        """
        return bool(ModelEndpoints._lite_llm["use"])

    @staticmethod
    def use_lite_llm_proxy() -> bool:
        """Check if LiteLLM proxy is enabled.

        Returns:
            True if LiteLLM proxy is enabled, False otherwise.

        """
        return bool(ModelEndpoints._lite_llm["use_proxy"])

    @staticmethod
    def get_lite_llm_config() -> tuple[str, str]:
        """Get LiteLLM configuration (API key and base URL).

        Returns:
            Tuple of (api_key, api_base).

        """
        api_key = ModelEndpoints._lite_llm["api_key"]
        api_base = ModelEndpoints._lite_llm["api_base"]
        return str(api_key) if api_key is not None else "", str(
            api_base
        ) if api_base is not None else ""

    @staticmethod
    def load_model_endpoints(file_path: str | None = None) -> list[ModelEndpoint]:
        """Load model endpoints from YAML configuration file.

        Args:
            file_path: Path to the model_endpoints.yml file. If None, uses the default path.

        Returns:
            List of loaded ModelEndpoint configurations.

        Raises:
            ValueError: If no default agent endpoint ID is found in the configuration.

        """
        if file_path is None:
            file_path = str(DEFAULT_MODEL_ENDPOINTS_PATH)
        full_path = Path(file_path)
        with full_path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)

        ModelEndpoints._default_agent_endpoint_id = data.get(
            "default_agent_endpoint_id",
            None,
        )

        ModelEndpoints._default_meta_agent_endpoint_id = data.get(
            "default_meta_agent_endpoint_id",
            None,
        )

        ModelEndpoints._default_utility_agent_endpoint_id = data.get(
            "default_utility_agent_endpoint_id",
            None,
        )

        if "ebiose" in data:
            ModelEndpoints._ebiose_api_config = EbioseAPIConfig(
                api_key=data["ebiose"].get("api_key", None),
                api_base=data["ebiose"].get("api_base", None),
            )

        if "lite_llm" in data:
            ModelEndpoints._lite_llm["use"] = data["lite_llm"].get("use", False)
            ModelEndpoints._lite_llm["use_proxy"] = data["lite_llm"].get(
                "use_proxy",
                False,
            )
            ModelEndpoints._lite_llm["api_key"] = data["lite_llm"].get("api_key", None)
            ModelEndpoints._lite_llm["api_base"] = data["lite_llm"].get(
                "api_base",
                None,
            )

        if ModelEndpoints._default_agent_endpoint_id is None:
            msg = "No default agent endpoint id found in model_endpoints.yml file. Check if 'default_agent_endpoint_id' is set."
            raise ValueError(msg)

        endpoints_data = data.get("endpoints", [])
        ModelEndpoints._endpoints = [
            ModelEndpoint(**endpoint) for endpoint in endpoints_data
        ]
        return ModelEndpoints._endpoints

    @staticmethod
    def get_model_endpoint(
        model_endpoint_id: str,
        file_path: str | None = None,
    ) -> ModelEndpoint | None:
        """Get a specific model endpoint by ID.

        Args:
            model_endpoint_id: The ID of the endpoint to retrieve.
            file_path: Optional path to the model endpoints configuration file.

        Returns:
            The ModelEndpoint if found, None otherwise.

        """
        if len(ModelEndpoints._endpoints) == 0:
            ModelEndpoints.load_model_endpoints(file_path)
        for endpoint in ModelEndpoints._endpoints:
            if endpoint.endpoint_id == model_endpoint_id:
                return endpoint
        return None

    @staticmethod
    def get_all_model_endpoints(file_path: str | None = None) -> list[ModelEndpoint]:
        """Get all configured model endpoints.

        Args:
            file_path: Optional path to the model endpoints configuration file.

        Returns:
            List of all available ModelEndpoint configurations.

        """
        if len(ModelEndpoints._endpoints) == 0:
            ModelEndpoints.load_model_endpoints(file_path)
        return ModelEndpoints._endpoints
