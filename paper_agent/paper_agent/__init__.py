"""
Paper Agent - 一个基于大语言模型的论文助手
"""

from .agent import PaperAgent
from .search import PaperSearcher
from .analyzer import PaperAnalyzer

__version__ = "0.2.0"
__author__ = "Paper Agent Team"
__all__ = ["PaperAgent", "PaperSearcher", "PaperAnalyzer"]