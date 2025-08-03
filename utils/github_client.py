import requests
import os
import logging
from typing import Dict, List, Optional

class GitHubClient:
    """GitHub API客户端，用于与GitHub API交互"""
    
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "StarTidy-Bot"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """发送HTTP请求到GitHub API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logging.error(f"GitHub API request failed: {e}")
            raise
    
    def get_starred_repos(self, username: str = None, per_page: int = 100) -> List[Dict]:
        """获取用户的starred repositories"""
        endpoint = f"users/{username}/starred" if username else "user/starred"
        
        repos = []
        page = 1
        
        while True:
            params = {"per_page": per_page, "page": page}
            page_repos = self._make_request("GET", endpoint, params=params)
            
            if not page_repos:
                break
                
            repos.extend(page_repos)
            
            # GitHub API最多返回1000条记录
            if len(page_repos) < per_page or len(repos) >= 1000:
                break
                
            page += 1
        
        return repos
    
    def get_user_lists(self) -> List[Dict]:
        """获取用户的star lists"""
        try:
            return self._make_request("GET", "user/starred/lists")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Star lists功能可能还没有完全推出
                logging.warning("Star lists API not available, returning empty list")
                return []
            raise
    
    def create_star_list(self, name: str, description: str = "") -> Dict:
        """创建新的star list"""
        data = {
            "name": name,
            "description": description
        }
        return self._make_request("POST", "user/starred/lists", data=data)
    
    def update_star_list(self, list_id: str, name: str = None, description: str = None) -> Dict:
        """更新star list"""
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        return self._make_request("PATCH", f"user/starred/lists/{list_id}", data=data)
    
    def add_repos_to_list(self, list_id: str, repo_ids: List[int]) -> Dict:
        """将repositories添加到star list"""
        data = {"starred_repository_ids": repo_ids}
        return self._make_request("PUT", f"user/starred/lists/{list_id}/items", data=data)
    
    def remove_repos_from_list(self, list_id: str, repo_ids: List[int]) -> Dict:
        """从star list中移除repositories"""
        data = {"starred_repository_ids": repo_ids}
        return self._make_request("DELETE", f"user/starred/lists/{list_id}/items", data=data)
    
    def get_user_info(self) -> Dict:
        """获取当前认证用户信息"""
        return self._make_request("GET", "user")


def create_github_client(token: str = None) -> GitHubClient:
    """创建GitHub客户端实例"""
    return GitHubClient(token)


if __name__ == "__main__":
    # 测试GitHub客户端
    try:
        client = create_github_client()
        user_info = client.get_user_info()
        print(f"Authenticated as: {user_info['login']}")
        
        # 获取前5个starred repos用于测试
        starred_repos = client.get_starred_repos()
        print(f"Found {len(starred_repos)} starred repositories")
        
        if starred_repos:
            print(f"First repo: {starred_repos[0]['full_name']}")
            
    except Exception as e:
        print(f"Error testing GitHub client: {e}")