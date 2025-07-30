"""
Background task manager interface for the OpenShift MCP Server.

This module defines the abstract interface for background task management.
"""

from abc import ABC, abstractmethod
from typing import Callable, Any, Dict, Optional, List
import asyncio
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskInfo:
    """Information about a background task."""
    task_id: str
    function: Callable
    args: tuple
    kwargs: dict
    created_at: datetime
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Any] = None
    error: Optional[str] = None


class IBackgroundTaskManager(ABC):
    """
    Abstract interface for background task managers.
    
    This interface defines the contract for background task management
    that can be used by the MCP server for non-blocking operations.
    """
    
    @abstractmethod
    async def schedule_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """
        Schedule a background task.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Task ID
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get the status of a background task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task information if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a background task.
        
        Args:
            task_id: The task ID to cancel
            
        Returns:
            True if task was cancelled, False if not found
        """
        pass
    
    @abstractmethod
    async def get_active_tasks(self) -> List[TaskInfo]:
        """
        Get list of active background tasks.
        
        Returns:
            List of active task information
        """
        pass
    
    @abstractmethod
    async def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed tasks older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed tasks
            
        Returns:
            Number of tasks cleaned up
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the task manager and cancel all pending tasks.
        """
        pass 