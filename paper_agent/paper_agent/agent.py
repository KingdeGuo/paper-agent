"""
论文助手主类
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

from .search import PaperSearcher
from .analyzer import PaperAnalyzer
from .utils import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """论文数据结构"""
    title: str
    authors: List[str]
    abstract: str
    url: str
    published_date: Optional[str] = None
    keywords: Optional[List[str]] = None


class PaperAgent:
    """
    论文助手主类，整合搜索和分析功能
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化论文助手
        
        Args:
            config_path: 配置文件路径
        """
        self.config_manager = ConfigManager(config_path)
        self.searcher = PaperSearcher(self.config_manager)
        self.analyzer = PaperAnalyzer(self.config_manager)
        
        # 设置日志
        log_level = getattr(logging, self.config_manager.get("log_level", "INFO").upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Paper]:
        """
        搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            
        Returns:
            论文列表
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
            
        logger.info(f"Searching papers for query: {query}")
        try:
            results = self.searcher.search(query, max_results)
            papers = [Paper(**result) for result in results]
            logger.info(f"Found {len(papers)} papers")
            return papers
        except Exception as e:
            logger.error(f"Error searching papers: {e}", exc_info=True)
            return []
    
    def summarize_paper(self, paper: Paper) -> Dict[str, Any]:
        """
        总结论文内容
        
        Args:
            paper: 论文对象
            
        Returns:
            论文总结信息
        """
        if not paper:
            logger.warning("No paper provided for summarization")
            return {}
            
        logger.info(f"Summarizing paper: {paper.title}")
        try:
            summary = self.analyzer.summarize(paper)
            return summary
        except Exception as e:
            logger.error(f"Error summarizing paper: {e}", exc_info=True)
            return {}
    
    def extract_key_points(self, paper: Paper) -> Dict[str, Any]:
        """
        提取论文关键点
        
        Args:
            paper: 论文对象
            
        Returns:
            关键点信息
        """
        if not paper:
            logger.warning("No paper provided for key points extraction")
            return {}
            
        logger.info(f"Extracting key points from paper: {paper.title}")
        try:
            key_points = self.analyzer.extract_key_points(paper)
            return key_points
        except Exception as e:
            logger.error(f"Error extracting key points: {e}", exc_info=True)
            return {}
    
    def compare_papers(self, papers: List[Paper]) -> Dict[str, Any]:
        """
        比较多个论文
        
        Args:
            papers: 论文列表
            
        Returns:
            论文比较结果
        """
        if not papers:
            logger.warning("No papers provided for comparison")
            return {}
            
        if len(papers) < 2:
            logger.warning("Need at least 2 papers to compare")
            return {"error": "Need at least 2 papers to compare"}
            
        logger.info(f"Comparing {len(papers)} papers")
        try:
            comparison = self.analyzer.compare_papers(papers)
            return comparison
        except Exception as e:
            logger.error(f"Error comparing papers: {e}", exc_info=True)
            return {}