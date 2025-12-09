"""
Models Package for Concept Studio

Contains data structures and business logic:
- Layer: Individual drawing layer with transform properties
- HistoryManager: Undo/redo system
- ProjectManager: Save/load projects

"""

from .layer import Layer
from .history import HistoryManager
from .project import ProjectManager

__all__ = ['Layer', 'HistoryManager', 'ProjectManager']
