"""Base agent class for interview agents."""
from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class BaseInterviewAgent(ABC):
    """Base class for all interview agents."""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        llm: Optional[ChatOpenAI] = None,
    ):
        """Initialize the agent with an LLM."""
        if llm:
            self.llm = llm
        else:
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=settings.openai_api_key,
            )
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Return the prompt template for this agent."""
        pass
    
    def format_prompt(self, **kwargs: Any) -> str:
        """Format the prompt template with provided values."""
        template = self.get_prompt_template()
        # Handle missing keys gracefully
        for key in re.findall(r'\{(\w+)\}', template):
            if key not in kwargs:
                kwargs[key] = "N/A"
        return template.format(**kwargs)
    
    async def invoke(self, **kwargs: Any) -> str:
        """Invoke the agent and return the raw response."""
        prompt = self.format_prompt(**kwargs)
        messages = [HumanMessage(content=prompt)]
        
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking {self.__class__.__name__}: {e}")
            raise
    
    def invoke_sync(self, **kwargs: Any) -> str:
        """Synchronous invoke for the agent."""
        prompt = self.format_prompt(**kwargs)
        messages = [HumanMessage(content=prompt)]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking {self.__class__.__name__}: {e}")
            raise
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from the LLM response."""
        try:
            # Try to extract JSON from the response
            # Sometimes LLM wraps JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response[:200]}... Error: {e}")
            # Return a default structure based on the agent type
            return self.get_default_response()
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return a default response structure. Override in subclasses."""
        return {}
