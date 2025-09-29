import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
# Look for .env in the project root
dotenv_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)


class MortgageBaseModel(BaseModel):
    """Base model with common configuration for all mortgage-related models"""
    model_config = ConfigDict(protected_namespaces=())


class DocumentType(str, Enum):
    DRIVER_LICENSE = "driver_license"
    BANK_STATEMENT = "bank_statement"
    TAX_STATEMENT = "tax_statement"
    PAY_STUB = "pay_stub"
    PASSPORT = "passport"


class AppMeta(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    session_name: str
    debug: bool = False


class LLMConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    base_url: str
    api_key: str
    default_model: str


class VectorDBConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    default_db_id: str
    provider: str
    embedding: str
    embedding_dimension: int
    default_chunk_size: int


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    host: str = "localhost"
    port: int = 5432
    database: str = "mortgage_db"
    username: str = "postgres"
    password: str = "password"


class Neo4jConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str  # Required from environment
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60
    enable_mcp: bool = True


class DocumentRequirementConfig(MortgageBaseModel):
    document_type: str  # Keep as string for YAML compatibility, validate at runtime
    quantity: int  # Alias for quantity_needed to maintain compatibility
    description: str
    
    @property
    def quantity_needed(self) -> int:
        """Alias for quantity to match models.DocumentRequirement"""
        return self.quantity
    
    def get_document_type_enum(self) -> DocumentType:
        """Convert string document_type to DocumentType enum"""
        try:
            return DocumentType(self.document_type)
        except ValueError:
            # Fallback for unknown document types
            return DocumentType.DRIVER_LICENSE  # or handle as needed


class ValidationRuleConfig(MortgageBaseModel):
    max_days_until_expiry: Optional[int] = None
    max_age_months: Optional[int] = None
    max_age_years: Optional[int] = None
    acceptable_alternatives: Optional[List[str]] = None
    required_fields: Optional[List[str]] = None


class StatusThresholdsConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    success_condition: str
    partial_condition: str
    minimum_success_ratio: float
    minimum_partial_ratio: float


class BusinessLogicConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    completion_messages: Dict[str, str]
    next_steps: Dict[str, List[str]]
    status_thresholds: StatusThresholdsConfig
    session_id_format: str
    application_id_format: str


class MortgageConfig(MortgageBaseModel):
    max_document_size_mb: int = 10
    allowed_document_types: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    validation_timeout_seconds: int = 30
    required_documents: Dict[str, List[DocumentRequirementConfig]]
    validation_rules: Dict[str, ValidationRuleConfig]
    business_logic: BusinessLogicConfig


class AgentInstructionsConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    chat_conversation: str
    mortgage_processing: str


class PromptsConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    validation_prompt_template: str
    document_template: str


class AgentSamplingParamsConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    strategy: Dict[str, Any]
    max_tokens: int


class AgentToolConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    tool_choice: str


class AgentDefinitionConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    name: str
    model: str
    instructions: str
    sampling_params: AgentSamplingParamsConfig
    max_infer_iters: int
    tools: List[str]
    tool_config: AgentToolConfig


class ResponseFormatConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    include_confidence_scores: bool = True
    include_processing_steps: bool = True
    include_agent_reasoning: bool = True
    max_reasoning_length: int = 1000
    timestamp_format: str = "ISO"


class AppConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    app: AppMeta
    llm: LLMConfig
    vector_db: VectorDBConfig
    database: DatabaseConfig
    neo4j: Neo4jConfig
    agent_instructions: AgentInstructionsConfig
    prompts: PromptsConfig
    agents: List[AgentDefinitionConfig]
    mortgage: MortgageConfig
    response_format: ResponseFormatConfig

    @staticmethod
    def _env_override(cfg: "AppConfig") -> "AppConfig":
        """Override config values with environment variables if present."""
        cfg.app.session_name = os.getenv("SESSION_NAME", cfg.app.session_name)
        cfg.app.debug = os.getenv("DEBUG", "false").lower() == "true"

        cfg.llm.base_url = os.getenv("LLAMA_BASE_URL", cfg.llm.base_url).rstrip("/")
        cfg.llm.default_model = os.getenv("MODEL_ID", cfg.llm.default_model)

        cfg.database.host = os.getenv("DB_HOST", cfg.database.host)
        cfg.database.port = int(os.getenv("DB_PORT", str(cfg.database.port)))
        cfg.database.database = os.getenv("DB_NAME", cfg.database.database)
        cfg.database.username = os.getenv("DB_USER", cfg.database.username)
        cfg.database.password = os.getenv("DB_PASSWORD", cfg.database.password)

        # Neo4j environment overrides
        cfg.neo4j.uri = os.getenv("NEO4J_URI", cfg.neo4j.uri)
        cfg.neo4j.username = os.getenv("NEO4J_USERNAME", cfg.neo4j.username)
        if os.getenv("NEO4J_PASSWORD"):
            cfg.neo4j.password = os.getenv("NEO4J_PASSWORD")
        cfg.neo4j.database = os.getenv("NEO4J_DATABASE", cfg.neo4j.database)
        cfg.neo4j.enable_mcp = os.getenv("NEO4J_ENABLE_MCP", "true").lower() == "true"

        return cfg

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AppConfig":
        """Load configuration from YAML file, then apply environment variable overrides."""
        if path is None:
            possible_paths = [
                os.getenv("CONFIG_PATH"),
                os.path.join(os.path.dirname(__file__), "config.yaml"),  # Same directory as config.py
                os.path.join(os.getcwd(), "utils", "config.yaml"),
                os.path.join(os.getcwd(), "config.yaml"),
                "config.yaml"
            ]
            
            path = None
            for p in possible_paths:
                if p and os.path.exists(p):
                    path = p
                    break
        
        if not path or not os.path.exists(path):
            raise RuntimeError(f"Config file not found. Tried locations: {possible_paths}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise RuntimeError(f"Config file is empty at {path}")
        
        try:
            cfg = cls(**data)
        except ValidationError as e:
            raise RuntimeError(f"Invalid config at {path}: {e}")
        
        return cls._env_override(cfg)

    def get_required_documents(self, loan_type: str) -> List[DocumentRequirementConfig]:
        """Get required documents for a specific loan type."""
        return self.mortgage.required_documents.get(loan_type, [])
    
    def get_validation_rules(self, document_type: str) -> Optional[ValidationRuleConfig]:
        """Get validation rules for a specific document type."""
        return self.mortgage.validation_rules.get(document_type)
    
    def format_processing_prompt(self, **kwargs) -> str:
        """Format the main processing prompt with provided variables."""
        return self.prompts.validation_prompt_template.format(**kwargs)
    
    def format_document_info(self, index: int, **kwargs) -> str:
        """Format document information using the template."""
        return self.prompts.document_template.format(index=index, **kwargs)
    
    def get_mortgage_agent(self) -> Optional[AgentDefinitionConfig]:
        """Get the mortgage processing agent configuration."""
        for agent in self.agents:
            if agent.name == "app":
                return agent
        return None
    
    def get_agent_instructions(self, agent_type: str = "mortgage_processing") -> str:
        """Get agent instructions for the specified type."""
        if agent_type == "mortgage_processing":
            return self.agent_instructions.mortgage_processing
        elif agent_type == "chat_conversation":
            return self.agent_instructions.chat_conversation
        return ""
    
    def get_sampling_params(self) -> Dict[str, Any]:
        """Get sampling parameters for the mortgage agent."""
        agent = self.get_mortgage_agent()
        if agent:
            return {
                "strategy": agent.sampling_params.strategy,
                "max_tokens": agent.sampling_params.max_tokens
            }
        return {"strategy": {"type": "greedy"}, "max_tokens": 2048}
    
    def get_session_id_format(self) -> str:
        """Get session ID format template."""
        return self.mortgage.business_logic.session_id_format
    
    def get_application_id_format(self) -> str:
        """Get application ID format template."""
        return self.mortgage.business_logic.application_id_format
    
    def get_status_thresholds(self) -> StatusThresholdsConfig:
        """Get status determination thresholds."""
        return self.mortgage.business_logic.status_thresholds
    
    def get_next_steps(self, step_type: str) -> List[str]:
        """Get next steps for a specific step type."""
        return self.mortgage.business_logic.next_steps.get(step_type, [])
    
    def get_completion_message(self, message_type: str) -> str:
        """Get completion message for a specific type."""
        return self.mortgage.business_logic.completion_messages.get(message_type, "Processing completed")


# =============================================================================
# LLM FACTORY FUNCTIONS (Integrated from core/llm.py)
# =============================================================================

def get_llm(temperature=0.1, max_tokens=1200):
    """Get properly configured LLM using new endpoint with proper tool calling support.
    
    Args:
        temperature: Temperature for LLM generation (default: 0.1 for tool calling)
        max_tokens: Maximum tokens for response (default: 1200)
    
    Returns:
        ChatOpenAI: Configured LLM instance using new endpoint from config.yaml
    """
    config = AppConfig.load()
    
    # Use the new endpoint with proper tool calling support
    return ChatOpenAI(
        base_url=config.llm.base_url,
        api_key=config.llm.api_key,
        model=config.llm.default_model,
        temperature=temperature,
        max_tokens=max_tokens
    )


def get_supervisor_llm():
    """Get LLM configured for supervisor agent (higher temperature, shorter responses)."""
    return get_llm(temperature=0.2, max_tokens=800)


def get_agent_llm():
    """Get LLM configured for regular agents (balanced settings)."""
    return get_llm(temperature=0.4, max_tokens=1500)


def get_grader_llm():
    """Get LLM configured for grading/evaluation tasks (low temperature for consistency)."""
    return get_llm(temperature=0.0, max_tokens=500)