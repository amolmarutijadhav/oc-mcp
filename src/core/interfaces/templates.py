"""
Template engine interface for the OpenShift MCP Server.

This module defines the abstract interface for response template implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class TemplateType(Enum):
    """Supported template types."""
    POD_LIST = "pod_list"
    POD_STATUS = "pod_status"
    POD_LOGS = "pod_logs"
    SERVICE_LIST = "service_list"
    SERVICE_STATUS = "service_status"
    DEPLOYMENT_LIST = "deployment_list"
    DEPLOYMENT_STATUS = "deployment_status"
    ERROR = "error"
    GENERAL = "general"


@dataclass
class TemplateContext:
    """Context for template rendering."""
    data: Dict[str, Any]
    query_type: str
    namespace: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None


class ITemplateEngine(ABC):
    """
    Abstract interface for template engines.
    
    This interface defines the contract for template engine implementations
    that can be used by the MCP server to format responses.
    """
    
    @abstractmethod
    def format_response(self, template_type: TemplateType, context: TemplateContext) -> str:
        """
        Format a response using the appropriate template.
        
        Args:
            template_type: The type of template to use
            context: The context for template rendering
            
        Returns:
            The formatted response
        """
        pass
    
    @abstractmethod
    def format_error(self, error_message: str, error_type: str = "general", 
                    context: Optional[TemplateContext] = None) -> str:
        """
        Format an error response.
        
        Args:
            error_message: The error message
            error_type: The type of error
            context: Optional context for error formatting
            
        Returns:
            The formatted error response
        """
        pass
    
    @abstractmethod
    def detect_template_type(self, query: str, data: Dict[str, Any]) -> TemplateType:
        """
        Detect the appropriate template type for a query and data.
        
        Args:
            query: The user query
            data: The data to be formatted
            
        Returns:
            The detected template type
        """
        pass
    
    @abstractmethod
    def register_template(self, template_type: TemplateType, template_class: type) -> None:
        """
        Register a new template class.
        
        Args:
            template_type: The template type
            template_class: The template class to register
        """
        pass
    
    @abstractmethod
    def get_available_templates(self) -> List[TemplateType]:
        """
        Get list of available template types.
        
        Returns:
            List of available template types
        """
        pass 