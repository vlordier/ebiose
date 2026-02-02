"""Ebiose cloud API client and response models."""

from __future__ import annotations

import json
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, cast

import requests
from loguru import logger
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime


# HTTP status codes
HTTP_NO_CONTENT = 204

# --- Type-Safe Response Handling ---
T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")  # For generic return types


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class APIBaseModel(BaseModel):
    """Base model for API models with camelCase aliases."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class ResponseValidator[T: BaseModel]:
    """Generic response validator using pydantic models."""

    @staticmethod
    def validate_response(
        response_data: dict[str, Any] | list[Any], model_type: type[T]
    ) -> T:
        """Validate and parse API response using pydantic model."""
        try:
            if isinstance(response_data, dict):
                return model_type.model_validate(response_data)
            # Fallback for unexpected response types
            return cast("T", response_data)
        except Exception as e:
            msg = f"Failed to validate response as {model_type.__name__}: {e}"
            raise ValueError(
                msg,
            ) from e

    @staticmethod
    def validate_list_response(
        response_data: list[Any] | dict[str, Any], model_type: type[T]
    ) -> list[T]:
        """Validate and parse list API responses."""
        if not isinstance(response_data, list):
            msg = f"Expected list response, got {type(response_data)}"
            raise TypeError(msg)

        try:
            return [
                model_type.model_validate(item)
                if isinstance(item, dict)
                else cast("T", item)
                for item in response_data
            ]
        except Exception as e:
            msg = f"Failed to validate list response as {model_type.__name__}: {e}"
            raise ValueError(
                msg,
            ) from e


# --- API Response Models ---
class APIResponse(BaseModel):
    """Base API response wrapper."""

    success: bool = True
    errors: list[str] | None = None


class SingleResponse[T: BaseModel](APIResponse):
    """Response containing a single item."""

    data: T | None = None


class ListResponse[T: BaseModel](APIResponse):
    """Response containing a list of items."""

    data: list[T] | None = None


class PaginatedResponse(ListResponse[T]):
    """Response with pagination information."""

    total: int | None = None
    page: int | None = None
    page_size: int | None = None


# --- Custom Exceptions ---
class EbioseCloudError(Exception):
    """Base exception for EbioseCloud API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        """Initialize a cloud API error with response metadata.

        Args:
            message: Error message.
            status_code: Optional HTTP status code.
            response_text: Optional response body or error payload.

        """
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

    def __str__(self) -> str:
        """Return a formatted error string with HTTP metadata.

        Returns:
            String representation including status code and response text.

        """
        return f"{super().__str__()} (Status Code: {self.status_code}, Response: {self.response_text or 'N/A'})"


class EbioseCloudHTTPError(EbioseCloudError):
    """Exception for HTTP errors (4xx, 5xx)."""


class EbioseCloudAuthError(EbioseCloudError):
    """Exception for authentication-related errors."""


# --- Enums ---
class Role(int, Enum):
    """Enum for User Roles."""

    USER = 1
    ADMIN = 2


class AgentType(int, Enum):
    """Enum for Agent Types."""

    STANDARD = 0
    GENETIC_OPERATOR = 1
    ARCHITECT = 2


# --- Pydantic Models (Updated based on swagger.json) ---


class AgentEngineInputModel(APIBaseModel):
    """Input model for agent engine configuration."""

    engine_type: str | None = None
    configuration: str | None = None


class AgentEngineOutputModel(APIBaseModel):
    """Output model for agent engine configuration."""

    engine_type: str | None = None
    configuration: str | None = None


class ApiKeyInputModel(APIBaseModel):
    """Input model for creating or updating an API key."""

    user_uuid: str | None = None
    expiration_date: datetime


class SelfApiKeyInputModel(APIBaseModel):
    """Input model for creating a new API key for the current user."""

    expiration_date: datetime


class EcosystemInputModel(APIBaseModel):
    """Input model for creating or updating an ecosystem."""

    community_credits_available: float


class ForgeCycleInputModel(APIBaseModel):
    """Input model for starting a new forge cycle."""

    n_agents_in_population: int
    n_selected_agents_from_ecosystem: int
    n_best_agents_to_return: int
    replacement_ratio: float
    tournament_size_ratio: float
    local_results_path: str | None = None
    budget: float


class ForgeInputModel(APIBaseModel):
    """Input model for creating or updating a forge."""

    name: str | None = None
    description: str | None = None
    ecosystem_uuid: str | None = None


class ForgeCycleSpendOutputModel(APIBaseModel):
    """Output model for the total spend of a forge cycle."""

    budget: float
    spent_budget: float
    remaining_budget: float


class LogEntryInputModel(APIBaseModel):
    """Input model for creating a new log entry."""

    index: str
    data: str


class SelfUserInputModel(APIBaseModel):
    """Input model for the current user updating their own profile."""

    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    github_id: str | None = None
    password: str | None = None


class SignupInputModel(APIBaseModel):
    """Input model for new user registration."""

    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    github_id: str | None = None
    password: str | None = None


class UserInputModel(APIBaseModel):
    """Input model for creating or updating a user (admin operation)."""

    role: Role
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    github_id: str | None = None
    credits_limit: float
    password: str | None = None


class UserOutputModel(APIBaseModel):
    """Output model representing a user's data."""

    uuid: str | None = None
    role: Role
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    github_id: str | None = None
    api_keys: list[ApiKeyOutputModel] | None = None
    credits_limit: float
    credits_used: float
    available_credits: float


class ApiKeyOutputModel(APIBaseModel):
    """Output model representing an API key."""

    uuid: str | None = None
    key: str | None = None
    created_at: datetime
    expiration_date: datetime
    user: UserOutputModel | None = None


class AgentInputModel(APIBaseModel):
    """Input model for creating or updating an agent."""

    name: str | None = None
    description: str | None = None
    architect_agent_uuid: str | None = None
    genetic_operator_agent_uuid: str | None = None
    agent_engine: AgentEngineInputModel | None = None
    description_embedding: list[float] | None = None
    parent_agent_uuids: list[str] | None = None
    origin_forge_cycle_uuid: str | None = None  # New field
    agent_type: AgentType


class AgentOutputModel(APIBaseModel):
    """Output model representing an agent."""

    uuid: str | None = None
    name: str | None = None
    description: str | None = None
    ecosystem: EcosystemOutputModel | None = None
    architect_agent_uuid: str | None = None
    genetic_operator_agent_uuid: str | None = None
    agent_engine: AgentEngineOutputModel | None = None
    description_embedding: list[float] | None = None
    compute_bank_in_dollars: float
    parent_agent_uuids: list[str] | None = None
    child_agent_uuids: list[str] | None = None
    origin_forge_cycle: ForgeCycleOutputModel | None = None  # New field
    agent_type: AgentType


class EcosystemOutputModel(APIBaseModel):
    """Output model representing an ecosystem."""

    uuid: str | None = None
    community_credits_available: float
    agents: list[AgentOutputModel] | None = None


class ForgeCycleOutputModel(APIBaseModel):
    """Output model representing a forge cycle's state. Updated structure."""

    uuid: str | None = None
    forge: ForgeOutputModel
    lite_llm_key: str | None = None
    n_agents_in_population: int
    n_selected_agents_from_ecosystem: int
    n_best_agents_to_return: int
    replacement_ratio: float
    tournament_size_ratio: float
    local_results_path: str | None = None
    budget: float
    spent_budget: float  # New field
    is_running: bool
    generated_agents_count: int | None = None  # New field


class ForgeOutputModel(APIBaseModel):
    """Output model representing a forge."""

    uuid: str | None = None
    name: str | None = None
    description: str | None = None
    forge_cycles: list[ForgeCycleOutputModel] | None = None


class LoginOutputModel(APIBaseModel):
    """Output model for a successful login."""

    user: UserOutputModel
    token: str | None = None


class NewCycleOutputModel(APIBaseModel):
    """Output model after starting a new forge cycle."""

    lite_llm_key: str | None = None
    forge_cycle_uuid: str | None = None
    base_url: str | None = None


class LogEntryOutputModel(APIBaseModel):
    """Output model for a log entry response."""

    id: str | None = None
    index: str | None = None
    success: bool
    message: str | None = None


# Rebuild models to resolve forward references
# This is crucial for Pydantic to correctly link models defined with string type hints.
UserOutputModel.model_rebuild()
ApiKeyOutputModel.model_rebuild()
AgentOutputModel.model_rebuild()
EcosystemOutputModel.model_rebuild()
ForgeCycleOutputModel.model_rebuild()
ForgeOutputModel.model_rebuild()
LoginOutputModel.model_rebuild()


# --- Core API Client ---
class EbioseCloudClient:
    """Core client for interacting with the EbioseCloud API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        bearer_token: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the EbioseCloudClient.

        Args:
            base_url: The base URL for the API.
            api_key: The API key for 'ApiKey' authentication.
            bearer_token: The Bearer token for 'Bearer' authentication.
            timeout: Request timeout in seconds.

        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.timeout = timeout
        if not self.api_key and not self.bearer_token:
            logger.debug(
                "Warning: EbioseCloudClient initialized without API key or Bearer token.",
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: bytes | str | None = None,
        json_data: dict[str, Any] | list[Any] | BaseModel | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an HTTP request."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Accept": "application/json"}
        if json_data is not None:
            headers["Content-Type"] = "application/json"

        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        elif self.api_key:
            headers["ApiKey"] = self.api_key

        try:
            # Pydantic v2 uses model_dump
            json_payload = json.loads(
                json.dumps(
                    json_data,
                    default=lambda o: o.model_dump(by_alias=True)
                    if isinstance(o, BaseModel)
                    else o,
                ),
            )

            response = requests.request(
                method,
                url,
                params=params,
                data=data,
                json=json_payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            if response.status_code == HTTP_NO_CONTENT or not response.content:
                return {}

            return cast("dict[str, Any] | list[Any]", response.json())

        except requests.exceptions.HTTPError as e:
            response_text = (
                str(e.response.text)
                if e.response is not None and e.response.text is not None
                else "No response body"
            )
            status_code = e.response.status_code if e.response else None
            error_details = response_text
            try:
                parsed_error = json.loads(response_text)
                if isinstance(parsed_error, dict):
                    error_details = str(
                        parsed_error.get(
                            "detail",
                            parsed_error.get("message", response_text),
                        ),
                    )
            except json.JSONDecodeError:
                pass
            msg = f"HTTP error occurred: {e.request.method} {e.request.url} - {error_details}"
            raise EbioseCloudHTTPError(
                msg,
                status_code=status_code,
                response_text=response_text,
            ) from e
        except requests.exceptions.RequestException as e:
            msg = f"Request failed: {e}"
            raise EbioseCloudError(msg) from e

    # --- ApiKey Endpoints ---
    def add_api_key(self, data: ApiKeyInputModel) -> bool:
        """Create a new API key.

        Args:
            data: API key input model with user and expiration details.

        Returns:
            True if successful.

        """
        self._request("POST", "/apikeys", json_data=data)
        return True

    def get_api_keys(self) -> list[ApiKeyOutputModel]:
        """Retrieve all API keys for the current user.

        Returns:
            List of API key output models.

        """
        response = self._request("GET", "/apikeys")
        if isinstance(response, list):
            return [ApiKeyOutputModel.model_validate(item) for item in response]
        return []

    def self_add_api_key(self, data: SelfApiKeyInputModel) -> bool:
        """Create a new API key for the current authenticated user.

        Args:
            data: API key input model with expiration details.

        Returns:
            True if successful.

        """
        self._request("POST", "/apikeys/self", json_data=data)
        return True

    def self_get_api_keys(self) -> list[ApiKeyOutputModel]:
        """Retrieve all API keys for the current authenticated user.

        Returns:
            List of API key output models.

        """
        return [
            ApiKeyOutputModel.model_validate(item)
            for item in self._request("GET", "/apikeys/self")
        ]

    def get_api_key(self, api_key_uuid: str) -> ApiKeyOutputModel:
        """Retrieve a specific API key by UUID.

        Args:
            api_key_uuid: UUID of the API key to retrieve.

        Returns:
            API key output model.

        """
        return ApiKeyOutputModel.model_validate(
            self._request("GET", f"/apikeys/{api_key_uuid}"),
        )

    def delete_api_key(self, api_key_uuid: str) -> None:
        """Delete an API key by UUID.

        Args:
            api_key_uuid: UUID of the API key to delete.

        """
        self._request("DELETE", f"/apikeys/{api_key_uuid}")

    def update_api_key(self, api_key_uuid: str, data: ApiKeyInputModel) -> None:
        """Update an existing API key.

        Args:
            api_key_uuid: UUID of the API key to update.
            data: Updated API key data.

        """
        self._request("PUT", f"/apikeys/{api_key_uuid}", json_data=data)

    def self_delete_api_key(self, api_key_uuid: str) -> None:
        """Delete an API key for the current user.

        Args:
            api_key_uuid: UUID of the API key to delete.

        """
        self._request("DELETE", f"/apikeys/self/{api_key_uuid}")

    # --- AuthEndpoints ---
    def login(self, email: str, password: str) -> LoginOutputModel:
        """Authenticate user with email and password.

        Args:
            email: User email address.
            password: User password.

        Returns:
            Login output model with authentication token.

        """
        return LoginOutputModel.model_validate(
            self._request(
                "GET",
                "/auth/login",
                params={"email": email, "password": password},
            ),
        )

    def login_github(self, code: str) -> LoginOutputModel:
        """Authenticate user with GitHub OAuth code.

        Args:
            code: GitHub authorization code.

        Returns:
            Login output model with authentication token.

        """
        return LoginOutputModel.model_validate(
            self._request("GET", "/auth/github/login", params={"code": code}),
        )

    def sign_up(self, data: SignupInputModel) -> UserOutputModel:
        """Register a new user account.

        Args:
            data: Signup input model with user details.

        Returns:
            User output model.

        """
        return UserOutputModel.model_validate(
            self._request("POST", "/auth/signup", json_data=data),
        )

    def self_update(self, data: SelfUserInputModel) -> UserOutputModel:
        """Update the current user's profile.

        Args:
            data: User input model with profile updates.

        Returns:
            Updated user output model.

        """
        return UserOutputModel.model_validate(
            self._request("PUT", "/auth/self-update", json_data=data),
        )

    def update_password(self, new_password: str) -> None:
        """Change the password for the current user.

        Args:
            new_password: New password for the user.

        """
        self._request(
            "PUT",
            "/auth/update-password",
            params={"newPassword": new_password},
        )

    def refresh_token(self, token: str) -> str:
        """Refresh the authentication token.

        Args:
            token: Current authentication token.

        Returns:
            New authentication token.

        """
        return str(self._request("GET", "/auth/refresh-token", params={"token": token}))

    def user_info(self) -> UserOutputModel:
        """Retrieve information about the current authenticated user.

        Returns:
            User output model with current user information.

        """
        return UserOutputModel.model_validate(self._request("GET", "/auth/user-info"))

    # --- EcosystemEndpoints ---
    def create_ecosystem(self, data: EcosystemInputModel) -> EcosystemOutputModel:
        """Create a new ecosystem.

        Args:
            data: Ecosystem input model with configuration.

        Returns:
            Created ecosystem output model.

        """
        return EcosystemOutputModel.model_validate(
            self._request("POST", "/ecosystems", json_data=data),
        )

    def list_ecosystems(self) -> list[EcosystemOutputModel]:
        """Retrieve all ecosystems.

        Returns:
            List of ecosystem output models.

        """
        return [
            EcosystemOutputModel.model_validate(item)
            for item in self._request("GET", "/ecosystems")
        ]

    def get_ecosystem(self, uuid: str) -> EcosystemOutputModel:
        """Retrieve a specific ecosystem by UUID.

        Args:
            uuid: UUID of the ecosystem to retrieve.

        Returns:
            Ecosystem output model.

        """
        return EcosystemOutputModel.model_validate(
            self._request("GET", f"/ecosystems/{uuid}"),
        )

    def update_ecosystem(
        self,
        uuid: str,
        data: EcosystemInputModel,
    ) -> EcosystemOutputModel:
        """Update an existing ecosystem.

        Args:
            uuid: UUID of the ecosystem to update.
            data: Updated ecosystem data.

        Returns:
            Updated ecosystem output model.

        """
        return EcosystemOutputModel.model_validate(
            self._request("PUT", f"/ecosystems/{uuid}", json_data=data),
        )

    def delete_ecosystem(self, uuid: str) -> None:
        """Delete an ecosystem by UUID.

        Args:
            uuid: UUID of the ecosystem to delete.

        """
        self._request("DELETE", f"/ecosystems/{uuid}")

    def add_agents_to_ecosystem(
        self,
        ecosystem_uuid: str,
        agents_data: list[AgentInputModel],
    ) -> None:
        """Add multiple agents to an ecosystem.

        Args:
            ecosystem_uuid: UUID of the target ecosystem.
            agents_data: List of agent input models to add.

        """
        self._request(
            "POST",
            f"/ecosystems/{ecosystem_uuid}/agents",
            json_data=agents_data,
        )

    def list_agents_in_ecosystem(self, ecosystem_uuid: str) -> list[AgentOutputModel]:
        """List all agents in an ecosystem.

        Args:
            ecosystem_uuid: UUID of the ecosystem.

        Returns:
            List of agent output models.

        """
        return [
            AgentOutputModel.model_validate(item)
            for item in self._request("GET", f"/ecosystems/{ecosystem_uuid}/agents")
        ]

    def delete_agents_from_ecosystem(
        self,
        ecosystem_uuid: str,
        agent_uuids: list[str],
    ) -> None:
        """Remove multiple agents from an ecosystem.

        Args:
            ecosystem_uuid: UUID of the ecosystem.
            agent_uuids: List of agent UUIDs to remove.

        """
        self._request(
            "DELETE",
            f"/ecosystems/{ecosystem_uuid}/agents",
            json_data=agent_uuids,
        )

    def get_agent_in_ecosystem(
        self,
        ecosystem_uuid: str,
        agent_uuid: str,
    ) -> AgentOutputModel:
        """Retrieve a specific agent from an ecosystem.

        Args:
            ecosystem_uuid: UUID of the ecosystem.
            agent_uuid: UUID of the agent to retrieve.

        Returns:
            Agent output model.

        """
        return AgentOutputModel.model_validate(
            self._request("GET", f"/ecosystems/{ecosystem_uuid}/agent/{agent_uuid}"),
        )

    def update_agent_in_ecosystem(
        self,
        ecosystem_uuid: str,
        agent_uuid: str,
        agent_data: AgentInputModel,
    ) -> AgentOutputModel:
        """Update an agent within an ecosystem.

        Args:
            ecosystem_uuid: UUID of the ecosystem.
            agent_uuid: UUID of the agent to update.
            agent_data: Updated agent data.

        Returns:
            Updated agent output model.

        """
        return AgentOutputModel.model_validate(
            self._request(
                "PUT",
                f"/ecosystems/{ecosystem_uuid}/agent/{agent_uuid}",
                json_data=agent_data,
            ),
        )

    def add_single_agent_to_ecosystem(
        self,
        ecosystem_uuid: str,
        agent_data: AgentInputModel,
    ) -> AgentOutputModel:
        """Add a single agent to an ecosystem.

        Args:
            ecosystem_uuid: UUID of the ecosystem.
            agent_data: Agent data to add.

        Returns:
            Created agent output model.

        """
        return AgentOutputModel.model_validate(
            self._request(
                "POST",
                f"/ecosystems/{ecosystem_uuid}/agent",
                json_data=agent_data,
            ),
        )

    # --- ForgeEndpoints ---
    def get_forges(self) -> list[ForgeOutputModel]:
        """Retrieve all forges.

        Returns:
            List of forge output models.

        """
        return [
            ForgeOutputModel.model_validate(item)
            for item in self._request("GET", "/forges")
        ]

    def add_forge(self, data: ForgeInputModel) -> ForgeOutputModel:
        """Create a new forge.

        Args:
            data: Forge input model with configuration.

        Returns:
            Created forge output model.

        """
        return ForgeOutputModel.model_validate(
            self._request("POST", "/forges", json_data=data),
        )

    def get_forge(self, forge_uuid: str) -> ForgeOutputModel:
        """Retrieve a specific forge by UUID.

        Args:
            forge_uuid: UUID of the forge.

        Returns:
            Forge output model.

        """
        return ForgeOutputModel.model_validate(
            self._request("GET", f"/forges/{forge_uuid}"),
        )

    def update_forge(self, forge_uuid: str, data: ForgeInputModel) -> ForgeOutputModel:
        """Update an existing forge.

        Args:
            forge_uuid: UUID of the forge to update.
            data: Updated forge data.

        Returns:
            Updated forge output model.

        """
        return ForgeOutputModel.model_validate(
            self._request("PUT", f"/forges/{forge_uuid}", json_data=data),
        )

    def delete_forge(self, forge_uuid: str) -> None:
        """Delete a forge by UUID.

        Args:
            forge_uuid: UUID of the forge to delete.

        """
        self._request("DELETE", f"/forges/{forge_uuid}")

    def start_new_forge_cycle(
        self,
        forge_uuid: str,
        data: ForgeCycleInputModel,
        *,
        override_key: bool | None = None,
    ) -> NewCycleOutputModel:
        """Start a new forge cycle for evolutionary optimization.

        Args:
            forge_uuid: UUID of the forge to run a cycle for.
            data: Forge cycle input model with population and settings.
            override_key: Whether to override budget key (optional).

        Returns:
            New cycle output model with cycle details.

        """
        params = {"overrideKey": override_key} if override_key is not None else {}
        return NewCycleOutputModel.model_validate(
            self._request(
                "POST",
                f"/forges/{forge_uuid}/cycles/start",
                params=params,
                json_data=data,
            ),
        )

    def end_forge_cycle(
        self,
        forge_cycle_uuid: str,
        agents_data: list[AgentInputModel],
    ) -> None:
        """End an ongoing forge cycle and submit final agents.

        Args:
            forge_cycle_uuid: UUID of the forge cycle to end.
            agents_data: Final list of agents to submit.

        """
        self._request(
            "POST",
            f"/forges/cycles/{forge_cycle_uuid}/end",
            json_data=agents_data,
        )

    def get_spend(self, forge_cycle_uuid: str) -> ForgeCycleSpendOutputModel:
        """Get budget spending information for a forge cycle.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.

        Returns:
            Forge cycle spend output model with budget details.

        """
        return ForgeCycleSpendOutputModel.model_validate(
            self._request("GET", f"/forges/cycles/{forge_cycle_uuid}/spend"),
        )

    def select_agents_for_forge_cycle(
        self,
        forge_cycle_uuid: str,
        nb_agents: int,
    ) -> list[AgentOutputModel]:
        """Select agents for a forge cycle.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            nb_agents: Number of agents to select.

        Returns:
            List of selected agent output models.

        """
        return [
            AgentOutputModel.model_validate(item)
            for item in self._request(
                "GET",
                f"/forges/cycles/{forge_cycle_uuid}/select-agents",
                params={"nbAgents": nb_agents},
            )
        ]

    def deduct_compute_banks_for_forge_cycle(
        self,
        forge_cycle_uuid: str,
        deductions: dict[str, float],
    ) -> None:
        """Deduct compute bank values for a forge cycle.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            deductions: Dictionary mapping agent UUIDs to deduction amounts.

        """
        self._request(
            "POST",
            f"/forges/cycles/{forge_cycle_uuid}/deduct-compute-banks",
            json_data=deductions,
        )

    def record_forge_cycle_usage(self, forge_cycle_uuid: str, cost: float) -> None:
        """Record usage cost for a forge cycle.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            cost: Cost amount to record.

        """
        self._request(
            "POST",
            f"/forges/cycles/{forge_cycle_uuid}/usage",
            params={"cost": cost},
        )

    def add_agent_during_forge_cycle(
        self,
        forge_cycle_uuid: str,
        data: AgentInputModel,
    ) -> AgentOutputModel:
        """Add a new agent to a forge cycle.

        Corresponds to POST /forges/cycles/{forgeCycleUuid}/agent.
        """
        return AgentOutputModel.model_validate(
            self._request(
                "POST",
                f"/forges/cycles/{forge_cycle_uuid}/agent",
                json_data=data,
            ),
        )

    def add_agents_during_forge_cycle(
        self,
        forge_cycle_uuid: str,
        agents_data: list[AgentInputModel],
    ) -> None:
        """Add multiple agents to a forge cycle.

        Corresponds to POST /forges/cycles/{forgeCycleUuid}/agents.
        """
        self._request(
            "POST",
            f"/forges/cycles/{forge_cycle_uuid}/agents",
            json_data=agents_data,
        )

    # --- Logging Endpoint (New) ---
    def add_log_entry(self, data: LogEntryInputModel) -> LogEntryOutputModel:
        """Corresponds to POST /logging."""
        return LogEntryOutputModel.model_validate(
            self._request("POST", "/logging", json_data=data),
        )

    # --- Users Endpoints ---
    def create_user(self, data: UserInputModel) -> UserOutputModel:
        """Create a new user.

        Args:
            data: User creation data.

        Returns:
            Created user output model.

        """
        return UserOutputModel.model_validate(
            self._request("POST", "/users", json_data=data),
        )

    def list_users(self) -> list[UserOutputModel]:
        """List all users.

        Returns:
            List of user output models.

        """
        return [
            UserOutputModel.model_validate(item)
            for item in self._request("GET", "/users")
        ]

    def get_user(self, user_uuid: str) -> UserOutputModel:
        """Get a user by UUID.

        Args:
            user_uuid: UUID of the user.

        Returns:
            User output model.

        """
        return UserOutputModel.model_validate(
            self._request("GET", f"/users/{user_uuid}"),
        )

    def update_user(self, user_uuid: str, data: UserInputModel) -> None:
        """Update a user.

        Args:
            user_uuid: UUID of the user.
            data: User update data.

        """
        self._request("PUT", f"/users/{user_uuid}", json_data=data)

    def delete_user(self, user_uuid: str) -> None:
        """Delete a user.

        Args:
            user_uuid: UUID of the user.

        """
        self._request("DELETE", f"/users/{user_uuid}")

    def get_user_by_email(self, email: str) -> UserOutputModel:
        """Get a user by email address.

        Args:
            email: Email address of the user.

        Returns:
            User output model.

        """
        return UserOutputModel.model_validate(
            self._request("GET", f"/users/email/{email}"),
        )


# --- Facade API Client ---
class EbioseAPIClient:
    """Facade client providing a high-level interface to the EbioseCloud API."""

    _client: EbioseCloudClient | None = None

    @classmethod
    def set_client_credentials(
        cls,
        base_url: str,
        api_key: str | None = None,
        bearer_token: str | None = None,
    ) -> None:
        """Set the API client credentials."""
        cls._client = EbioseCloudClient(
            base_url=base_url,
            api_key=api_key,
            bearer_token=bearer_token,
        )
        logger.debug(f"EbioseCloudClient initialized for base URL: {base_url}")

    @classmethod
    def _get_client(cls) -> EbioseCloudClient:
        """Ensure client initialization."""
        if cls._client is None:
            msg = "Client not initialized. Call EbioseAPIClient.set_client_credentials() first."
            raise EbioseCloudAuthError(
                msg,
            )
        return cls._client

    @classmethod
    def _handle_request(
        cls,
        action_description: str,
        api_call: Callable[..., R],
        *args: object,
        **kwargs: object,
    ) -> R:
        """Handle request generically."""
        try:
            return api_call(*args, **kwargs)
        except EbioseCloudError as e:
            logger.debug(f"An API error occurred while {action_description}: {e}")
            raise
        except Exception as e:
            logger.debug(
                f"An unexpected error occurred while {action_description}: {e}",
            )
            raise

    # --- ApiKey Facade ---
    @classmethod
    def add_new_api_key(cls, data: ApiKeyInputModel) -> bool:
        """Create a new API key via the facade.

        Args:
            data: API key input model.

        Returns:
            True if the API key was created successfully.

        """
        return bool(
            cls._handle_request(
                "add new API key",
                cls._get_client().add_api_key,
                data=data,
            ),
        )

    # --- Forge Facade (with new methods) ---
    @classmethod
    def list_all_forges(cls) -> ListResponse[ForgeOutputModel]:
        """List all forges via the facade.

        Returns:
            ListResponse containing forge output models.

        """
        response = cls._handle_request("list all forges", cls._get_client().get_forges)
        return ListResponse(data=response)

    @classmethod
    def add_new_forge(cls, data: ForgeInputModel) -> SingleResponse[ForgeOutputModel]:
        """Create a new forge via the facade.

        Args:
            data: Forge input model.

        Returns:
            SingleResponse containing the created forge.

        """
        response = cls._handle_request(
            "add new forge",
            cls._get_client().add_forge,
            data=data,
        )
        return SingleResponse(data=response)

    @classmethod
    def get_specific_forge(cls, forge_uuid: str) -> SingleResponse[ForgeOutputModel]:
        """Retrieve a forge by UUID via the facade.

        Args:
            forge_uuid: UUID of the forge.

        Returns:
            SingleResponse containing the forge.

        """
        response = cls._handle_request(
            f"get forge {forge_uuid}",
            cls._get_client().get_forge,
            forge_uuid=forge_uuid,
        )
        return SingleResponse(data=response)

    @classmethod
    def modify_forge(cls, forge_uuid: str, data: ForgeInputModel) -> ForgeOutputModel:
        """Update a forge via the facade.

        Args:
            forge_uuid: UUID of the forge.
            data: Updated forge data.

        Returns:
            Updated forge output model.

        """
        return cls._handle_request(
            f"update forge {forge_uuid}",
            cls._get_client().update_forge,
            forge_uuid=forge_uuid,
            data=data,
        )

    @classmethod
    def remove_forge(cls, forge_uuid: str) -> None:
        """Delete a forge via the facade.

        Args:
            forge_uuid: UUID of the forge to delete.

        """
        cls._handle_request(
            f"delete forge {forge_uuid}",
            cls._get_client().delete_forge,
            forge_uuid=forge_uuid,
        )

    @classmethod
    def start_new_forge_cycle(
        cls,
        forge_uuid: str,
        data: ForgeCycleInputModel,
        *,
        override_key: bool | None = None,
    ) -> NewCycleOutputModel:
        """Start a new forge cycle via the facade.

        Args:
            forge_uuid: UUID of the forge.
            data: Forge cycle input model.
            override_key: Whether to override budget key.

        Returns:
            New cycle output model.

        """
        return cls._handle_request(
            f"start new forge cycle for forge {forge_uuid}",
            cls._get_client().start_new_forge_cycle,
            forge_uuid=forge_uuid,
            data=data,
            override_key=override_key,
        )

    @classmethod
    def conclude_forge_cycle(
        cls,
        forge_cycle_uuid: str,
        agents_data: list[AgentInputModel],
    ) -> None:
        """End a forge cycle and submit final agents via the facade.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            agents_data: List of final agents.

        """
        cls._handle_request(
            f"end forge cycle {forge_cycle_uuid}",
            cls._get_client().end_forge_cycle,
            forge_cycle_uuid=forge_cycle_uuid,
            agents_data=agents_data,
        )

    @classmethod
    def get_forge_cycle_spend(cls, forge_cycle_uuid: str) -> ForgeCycleSpendOutputModel:
        """Retrieve spend information for a forge cycle via the facade.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.

        Returns:
            Forge cycle spend output model.

        """
        return cls._handle_request(
            f"get spend for forge cycle {forge_cycle_uuid}",
            cls._get_client().get_spend,
            forge_cycle_uuid=forge_cycle_uuid,
        )

    @classmethod
    def log_forge_cycle_usage(cls, forge_cycle_uuid: str, cost: float) -> None:
        """Record usage cost for a forge cycle via the facade.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            cost: Cost value to record.

        """
        cls._handle_request(
            f"record usage for forge cycle {forge_cycle_uuid}",
            cls._get_client().record_forge_cycle_usage,
            forge_cycle_uuid=forge_cycle_uuid,
            cost=cost,
        )

    @classmethod
    def pick_agents_for_forge_cycle(
        cls,
        forge_cycle_uuid: str,
        nb_agents: int,
    ) -> list[AgentOutputModel]:
        """Select agents for a forge cycle via the facade.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            nb_agents: Number of agents to select.

        Returns:
            List of selected agent output models.

        """
        return cls._handle_request(
            f"select agents for forge cycle {forge_cycle_uuid}",
            cls._get_client().select_agents_for_forge_cycle,
            forge_cycle_uuid=forge_cycle_uuid,
            nb_agents=nb_agents,
        )

    @classmethod
    def make_deduct_compute_banks_for_forge_cycle(
        cls,
        forge_cycle_uuid: str,
        deductions: dict[str, float],
    ) -> None:
        """Deduct compute banks for a forge cycle via the facade.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.
            deductions: Mapping of agent UUIDs to deduction values.

        """
        cls._handle_request(
            f"deduct compute banks for forge cycle {forge_cycle_uuid}",
            cls._get_client().deduct_compute_banks_for_forge_cycle,
            forge_cycle_uuid=forge_cycle_uuid,
            deductions=deductions,
        )

    @classmethod
    def add_agent_during_cycle(
        cls,
        forge_cycle_uuid: str,
        agent_data: AgentInputModel,
    ) -> AgentOutputModel:
        """Add a single agent during an active forge cycle."""
        return cls._handle_request(
            f"add agent to active forge cycle {forge_cycle_uuid}",
            cls._get_client().add_agent_during_forge_cycle,
            forge_cycle_uuid=forge_cycle_uuid,
            data=agent_data,
        )

    @classmethod
    def add_agents_during_cycle(
        cls,
        forge_cycle_uuid: str,
        agents_data: list[AgentInputModel],
    ) -> None:
        """Add multiple agents during an active forge cycle."""
        cls._handle_request(
            f"add agents to active forge cycle {forge_cycle_uuid}",
            cls._get_client().add_agents_during_forge_cycle,
            forge_cycle_uuid=forge_cycle_uuid,
            agents_data=agents_data,
        )

    # --- Logging Facade (New) ---
    @classmethod
    def log_message(cls, data: LogEntryInputModel) -> LogEntryOutputModel:
        """Send a log entry to the logging service."""
        # Note: A more specific description might be better depending on usage.
        return cls._handle_request(
            f"send log entry to index '{data.index}'",
            cls._get_client().add_log_entry,
            data=data,
        )
