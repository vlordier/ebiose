"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from langchain_community.chat_models import ChatLiteLLM

try:
    from langchain_community.chat_models.azureml_endpoint import (
        AzureMLChatOnlineEndpoint,
        AzureMLEndpointApiType,
        CustomOpenAIChatContentFormatter,
    )
except ImportError:
    AzureMLChatOnlineEndpoint = None
    AzureMLEndpointApiType = None
    CustomOpenAIChatContentFormatter = None

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from litellm.cost_calculator import cost_per_token
from loguru import logger
from openai import RateLimitError

from ebiose.core.llm_api import LLMApi, LLMAPIConfig
from ebiose.core.model_endpoint import ModelEndpoint, ModelEndpoints

# Optional provider imports - wrap in try/except for graceful degradation
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_huggingface import HuggingFaceEndpoint
except ImportError:
    HuggingFaceEndpoint = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

if TYPE_CHECKING:
    from langchain_core.messages import AnyMessage
    from pydantic import SecretStr

# Type alias for all possible LLM return types
LLMType = (
    ChatOpenAI
    | ChatLiteLLM
    | AzureChatOpenAI
    | AzureMLChatOnlineEndpoint
    | ChatAnthropic
    | HuggingFaceEndpoint
    | ChatGoogleGenerativeAI
    | ChatOllama
)


@dataclass
class LLMCallConfig:
    """Configuration for LLM calls to reduce parameter count."""

    model_endpoint_id: str
    messages: list
    agent_id: str
    temperature: float = 0.0
    max_tokens: int = 4096
    tools: list | None = None


@dataclass
class LLMProviderConfig:
    """Configuration for LLM provider creation."""

    model_endpoint: ModelEndpoint
    model_endpoint_id: str
    temperature: float
    max_tokens: int
    request_timeout: int | float
    max_retries: int


# --- Type-Safe Helper Functions ---
def safe_get_secret_value(secret: str | SecretStr | None) -> str | None:
    """Safely extract secret value from potentially None SecretStr."""
    if secret is None:
        return None
    if hasattr(secret, "get_secret_value"):
        return cast("str", secret.get_secret_value())
    return str(secret) if secret else None


class LangGraphLLMApiError(Exception):
    """Custom exception for errors during LLM calls."""

    def __init__(
        self,
        message: str,
        original_exception: Exception | None = None,
        llm_identifier: str | None = None,
    ) -> None:
        super().__init__(message)
        self.original_exception = original_exception
        self.llm_identifier = llm_identifier

    def __str__(self) -> str:
        error_msg = "LangGraphLLMApiError"
        if self.llm_identifier:
            error_msg += f" (LLM: {self.llm_identifier})"
        error_msg += f": {super().__str__()}"
        if self.original_exception:
            orig_traceback = traceback.format_exception(
                type(self.original_exception),
                self.original_exception,
                self.original_exception.__traceback__,
            )
            error_msg += f"\n--- Caused by ---\n{''.join(orig_traceback)}"
        return error_msg


class LangGraphLLMApi(LLMApi):
    @classmethod
    def initialize(
        cls,
        mode: Literal["local", "cloud"],
        lite_llm_api_key: str | None = None,
        lite_llm_api_base: str | None = None,
        llm_api_config: LLMAPIConfig | None = None,
    ) -> type[LangGraphLLMApi]:
        cls.mode = mode
        cls.lite_llm_api_key = lite_llm_api_key

        # Set lite_llm_api_base based on mode and available configuration
        if lite_llm_api_base is not None:
            # Use provided base URL (typically from cloud API)
            cls.lite_llm_api_base = lite_llm_api_base
        elif mode == "local" and ModelEndpoints.use_lite_llm():
            # Use local configuration from model_endpoints.yml
            _, configured_base = ModelEndpoints.get_lite_llm_config()
            cls.lite_llm_api_base = configured_base
        else:
            # Keep as None - no LiteLLM base URL available
            cls.lite_llm_api_base = None

        if llm_api_config is not None:
            cls._llm_api_config = llm_api_config

        return cls

    @classmethod
    def _get_llm(
        cls,
        model_endpoint_id: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMType:
        """Get the LLM model from the model endpoint id.

        Args:
            model_endpoint_id: The ID of the model endpoint to use
            temperature: Temperature parameter for the LLM
            max_tokens: Maximum number of tokens allowed in the response

        Returns:
            The LLM model

        """
        request_timeout = cls._llm_api_config.request_timeout_in_minutes * 60
        max_retries = cls._llm_api_config.max_retries

        model_endpoint = ModelEndpoints.get_model_endpoint(model_endpoint_id)

        if model_endpoint is None:
            msg = f"Model endpoint '{model_endpoint_id}' not found"
            raise ValueError(msg)

        # Cloud mode handling
        if cls.mode == "cloud":
            return cls._create_cloud_llm(model_endpoint_id, temperature, max_tokens)

        # LiteLLM handling
        if ModelEndpoints.use_lite_llm_proxy():
            return cls._create_litellm_proxy_llm(model_endpoint_id, temperature, max_tokens)

        if ModelEndpoints.use_lite_llm():
            return cls._create_litellm_llm(model_endpoint, temperature, max_tokens, request_timeout, max_retries)

        # Provider-specific handling
        provider_config = LLMProviderConfig(
            model_endpoint=model_endpoint,
            model_endpoint_id=model_endpoint_id,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
        return cls._create_provider_llm(provider_config)

    @classmethod
    def _create_cloud_llm(cls, model_endpoint_id: str, temperature: float, max_tokens: int) -> ChatOpenAI:
        """Create LLM for cloud mode."""
        return ChatOpenAI(
            openai_api_key=cls.lite_llm_api_key,
            openai_api_base=cls.lite_llm_api_base,
            model=model_endpoint_id,
            temperature=temperature if model_endpoint_id != "azure/o3-mini" else 1.0,
            max_tokens=max_tokens,
        )

    @classmethod
    def _create_litellm_proxy_llm(cls, model_endpoint_id: str, temperature: float, max_tokens: int) -> ChatOpenAI:
        """Create LLM for LiteLLM proxy mode."""
        lite_llm_api_key, lite_llm_api_base = ModelEndpoints.get_lite_llm_config()
        return ChatOpenAI(
            openai_api_key=lite_llm_api_key,
            openai_api_base=lite_llm_api_base,
            model=model_endpoint_id,
            temperature=temperature if model_endpoint_id != "azure/o3-mini" else 1.0,
            max_tokens=max_tokens,
        )

    @classmethod
    def _create_litellm_llm(
        cls,
        model_endpoint: ModelEndpoint,
        temperature: float,
        max_tokens: int,
        request_timeout: float,
        max_retries: int,
    ) -> ChatLiteLLM:
        """Create LLM using LiteLLM."""
        return ChatLiteLLM(
            model=f"azure/{model_endpoint.deployment_name}",
            azure_api_key=safe_get_secret_value(model_endpoint.api_key),
            api_base=safe_get_secret_value(model_endpoint.endpoint_url),
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=request_timeout,
            max_retries=max_retries,
        )

    @classmethod
    def _create_provider_llm(cls, config: LLMProviderConfig) -> LLMType:
        """Create LLM based on provider using strategy mapping."""
        provider = config.model_endpoint.provider
        model_endpoint = config.model_endpoint
        model_endpoint_id = config.model_endpoint_id
        temperature = config.temperature
        max_tokens = config.max_tokens
        request_timeout = config.request_timeout
        max_retries = config.max_retries

        # Define provider-specific creation strategies
        provider_strategies = {
            "OpenAI": lambda: ChatOpenAI(
                model=model_endpoint_id,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=safe_get_secret_value(model_endpoint.api_key),
            ),
            "OpenRouter": lambda: ChatOpenAI(
                openai_api_base=safe_get_secret_value(model_endpoint.endpoint_url),
                model=model_endpoint_id,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=safe_get_secret_value(model_endpoint.api_key),
            ),
            "AzureOpenAI": lambda: AzureChatOpenAI(
                azure_deployment=model_endpoint.deployment_name,
                azure_endpoint=safe_get_secret_value(model_endpoint.endpoint_url),
                openai_api_key=safe_get_secret_value(model_endpoint.api_key),
                openai_api_version=model_endpoint.api_version,
                temperature=temperature,
                request_timeout=request_timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
            ),
            "Azure AI": lambda: cast("Any", AzureMLChatOnlineEndpoint)(
                endpoint_url=safe_get_secret_value(model_endpoint.endpoint_url),
                endpoint_api_type=cast("Any", AzureMLEndpointApiType).serverless,
                endpoint_api_key=safe_get_secret_value(model_endpoint.api_key),
                content_formatter=cast("Any", CustomOpenAIChatContentFormatter)(),
                timeout=request_timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
                model_kwargs={"temperature": temperature},
            ),
        }

        # Providers requiring optional imports
        optional_providers = {
            "Anthropic": (
                ChatAnthropic,
                "langchain_anthropic not installed. Install with: pip install langchain-anthropic",
                lambda: cast("Any", ChatAnthropic)(
                    model=model_endpoint_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=safe_get_secret_value(model_endpoint.api_key),
                ),
            ),
            "HuggingFace": (
                HuggingFaceEndpoint,
                "langchain_huggingface not installed. Install with: pip install langchain-huggingface",
                lambda: cast("Any", HuggingFaceEndpoint)(
                    repo_id=model_endpoint_id,
                    task="text-generation",
                    max_new_tokens=max_tokens,
                ),
            ),
            "Google": (
                ChatGoogleGenerativeAI,
                "langchain_google_genai not installed. Install with: pip install langchain-google-genai",
                lambda: cast("Any", ChatGoogleGenerativeAI)(
                    model=model_endpoint_id,
                    google_api_key=safe_get_secret_value(model_endpoint.api_key),
                ),
            ),
            "Ollama": (
                ChatOllama,
                "langchain_ollama not installed. Install with: pip install langchain-ollama",
                lambda: cast("Any", ChatOllama)(
                    model=model_endpoint_id.replace("ollama/", ""),
                    temperature=temperature,
                    num_predict=max_tokens,
                    base_url=safe_get_secret_value(model_endpoint.endpoint_url),
                ),
            ),
        }

        # Try standard providers first
        if provider in provider_strategies:
            return provider_strategies[provider]()

        # Try optional providers
        if provider in optional_providers:
            provider_class, error_msg, factory = optional_providers[provider]
            if provider_class is None:
                raise ImportError(error_msg)
            return factory()

        # Unknown provider
        msg = f"Unsupported provider: {provider}"
        raise ValueError(msg)

    @classmethod
    async def _call_llm(
        cls,
        model_endpoint_id: str,
        messages: list[AnyMessage],
        temperature: float,
        max_tokens: int,
        tools: list | None = None,
    ) -> AnyMessage:
        """Call the LLM using Langchain's AzureChatOpenAI.

        Args:
            model_endpoint_id: The ID of the model endpoint to use
            messages: List of messages to send to the LLM
            temperature: Temperature parameter for the LLM
            max_tokens: Maximum number of tokens allowed in the response
            tools: List of tools to bind to the LLM

        Returns:
            The LLM's response text

        """
        if tools is None:
            tools = []

        llm = cls._get_llm(model_endpoint_id, temperature, max_tokens)

        # Ensure llm is not None
        if llm is None:
            msg = f"Failed to initialize LLM for model endpoint '{model_endpoint_id}'"
            raise LangGraphLLMApiError(msg, llm_identifier=model_endpoint_id)

        # Add tools
        if tools:
            # We use cast here because LLMType is a union that technically includes NoneType
            # due to optional imports, but we've already checked for None above.
            llm = cast("Any", llm).bind_tools(tools=tools)

        # Call LLM
        response = await cast("Any", llm).with_retry(
            retry_if_exception_type=(RateLimitError,),  # APITimeoutError
            wait_exponential_jitter=True,
            stop_after_attempt=10,
        ).ainvoke(messages)
        return cast("AnyMessage", response)

    @classmethod
    async def process_llm_call(cls, config: object) -> AnyMessage:
        """Process LLM call with config object.

        Args:
            config: LLMCallConfig containing all call parameters

        Returns:
            The LLM response message

        """
        if not isinstance(config, LLMCallConfig):
            msg = f"Expected LLMCallConfig, got {type(config)}"
            raise TypeError(msg)

        def _check_response(resp: AnyMessage | None, endpoint_id: str) -> None:
            if resp is None:
                msg = "Empty response from LLM"
                raise LangGraphLLMApiError(
                    msg,
                    RuntimeError("Empty response"),
                    endpoint_id,
                )

        try:
            # Record the request and tokens
            response = await cls._call_llm(
                config.model_endpoint_id,
                config.messages,
                config.temperature,
                config.max_tokens,
                config.tools or None,
            )

            _check_response(response, config.model_endpoint_id)

            completion_tokens = response.response_metadata["token_usage"].get(
                "completion_tokens",
                0,
            )
            prompt_tokens = response.response_metadata["token_usage"].get(
                "prompt_tokens",
                0,
            )

            cost_tuple = cost_per_token(
                model=config.model_endpoint_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            cost = sum(cost_tuple)
            cls.add_agent_cost(config.agent_id, cost)

        except Exception as e:
            logger.debug(f"Error when calling {config.model_endpoint_id}: {e!s}")
            msg = "Failed during call to an LLM API"
            raise LangGraphLLMApiError(msg, e, config.model_endpoint_id) from e
        else:
            return response
