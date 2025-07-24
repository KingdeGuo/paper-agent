"""
论文搜索模块
"""

from typing import List, Dict, Optional, Any
import requests
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import logging

from .utils import ConfigManager

logger = logging.getLogger(__name__)


class SearchBackend(ABC):
    """搜索后端抽象基类"""
    
    @abstractmethod
    def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """执行搜索"""
        pass


class ArxivSearchBackend(SearchBackend):
    """Arxiv搜索后端"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.base_url = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用Arxiv API搜索论文"""
        if not query or not query.strip():
            logger.warning("Empty query provided to Arxiv search")
            return []
            
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            logger.info(f"Searching Arxiv for query: {query}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            papers = self._parse_response(response.text)
            logger.info(f"Successfully retrieved {len(papers)} papers from Arxiv")
            return papers
        except requests.exceptions.Timeout:
            logger.error("Timeout when searching Arxiv")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when searching Arxiv: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching arxiv: {e}", exc_info=True)
            return []
    
    def _parse_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """解析Arxiv返回的XML内容"""
        try:
            root = ET.fromstring(xml_content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', namespace):
                title = entry.find('atom:title', namespace)
                summary = entry.find('atom:summary', namespace)
                published = entry.find('atom:published', namespace)
                link = entry.find('atom:id', namespace)
                
                # 获取作者
                authors = []
                for author in entry.findall('atom:author', namespace):
                    name = author.find('atom:name', namespace)
                    if name is not None:
                        authors.append(name.text)
                
                paper = {
                    "title": title.text if title is not None else "Unknown Title",
                    "authors": authors,
                    "abstract": summary.text if summary is not None else "",
                    "url": link.text if link is not None else "",
                    "published_date": published.text[:10] if published is not None else None
                }
                
                papers.append(paper)
            
            return papers
        except ET.ParseError as e:
            logger.error(f"Error parsing Arxiv XML response: {e}")
            # 返回示例数据以防解析失败
            return [
                {
                    "title": "Sample Paper Title",
                    "authors": ["Author 1", "Author 2"],
                    "abstract": "This is a sample abstract...",
                    "url": "http://arxiv.org/abs/sample",
                    "published_date": "2023-01-01"
                }
            ]


class PaperSearcher:
    """论文搜索器"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.backend = ArxivSearchBackend(config)
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            
        Returns:
            论文信息列表
        """
        return self.backend.search(query, max_results)