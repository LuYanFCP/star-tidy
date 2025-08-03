import logging
from typing import Dict, List, Optional, Tuple
from utils.github_client import GitHubClient
from utils.call_llm import call_llm_with_config

class StarListManager:
    """Manage GitHub star lists creation, updates, and maintenance"""
    
    def __init__(self, github_client: GitHubClient, config: Dict = None):
        self.github_client = github_client
        self.config = config or {}
        self._list_cache = {}
        self.summary_options = {
            "auto_complete": True,  # Auto-complete missing descriptions
            "enhance_existing": True,  # Enhance existing descriptions
            "use_ai_summary": True,  # Use AI to generate summaries
            "include_stats": True,  # Include repository statistics
        }
    
    def get_existing_lists(self) -> List[Dict]:
        """Get existing star lists"""
        try:
            lists = self.github_client.get_user_lists()
            self._list_cache = {lst["name"]: lst for lst in lists}
            return lists
        except Exception as e:
            logging.warning(f"Failed to fetch existing star lists: {e}")
            return []
    
    def create_or_update_list(self, list_name: str, description: str = "", 
                            repos_to_add: List[Dict] = None) -> Dict:
        """创建或更新star list"""
        repos_to_add = repos_to_add or []
        
        try:
            # Check if list already exists
            existing_list = self._list_cache.get(list_name)
            
            if existing_list:
                # Update existing list
                result = self._update_existing_list(existing_list, description, repos_to_add)
            else:
                # Create new list
                result = self._create_new_list(list_name, description, repos_to_add)
            
            return result
        except Exception as e:
            logging.error(f"Failed to create/update list '{list_name}': {e}")
            return {"success": False, "error": str(e)}
    
    def _create_new_list(self, list_name: str, description: str, 
                        repos_to_add: List[Dict]) -> Dict:
        """Create new star list"""
        try:
            # Create list
            new_list = self.github_client.create_star_list(list_name, description)
            list_id = new_list["id"]
            
            # Add repositories
            if repos_to_add:
                repo_ids = [repo["id"] for repo in repos_to_add]
                self.github_client.add_repos_to_list(list_id, repo_ids)
            
            # Update cache
            self._list_cache[list_name] = new_list
            
            logging.info(f"Created new star list '{list_name}' with {len(repos_to_add)} repositories")
            
            return {
                "success": True,
                "action": "created",
                "list_id": list_id,
                "repos_added": len(repos_to_add)
            }
            
        except Exception as e:
            logging.error(f"Failed to create list '{list_name}': {e}")
            raise
    
    def _update_existing_list(self, existing_list: Dict, description: str,
                            repos_to_add: List[Dict]) -> Dict:
        """Update existing star list"""
        try:
            list_id = existing_list["id"]
            list_name = existing_list["name"]
            
            # Update description (if provided)
            if description and description != existing_list.get("description", ""):
                self.github_client.update_star_list(list_id, description=description)
            
            # Add new repositories
            repos_added = 0
            if repos_to_add:
                # Get current repo IDs in list (simplified handling, may need API call in practice)
                repo_ids_to_add = [repo["id"] for repo in repos_to_add]
                if repo_ids_to_add:
                    self.github_client.add_repos_to_list(list_id, repo_ids_to_add)
                    repos_added = len(repo_ids_to_add)
            
            logging.info(f"Updated star list '{list_name}' with {repos_added} repositories")
            
            return {
                "success": True,
                "action": "updated",
                "list_id": list_id,
                "repos_added": repos_added
            }
            
        except Exception as e:
            logging.error(f"Failed to update list '{existing_list['name']}': {e}")
            raise
    
    def organize_repos_by_category(self, classification_results: Dict[str, Dict],
                                 starred_repos: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize repositories by classification results"""
        organized = {}
        
        # Create repo lookup mapping
        repo_map = {repo["full_name"]: repo for repo in starred_repos}
        
        for repo_full_name, classification in classification_results.items():
            category = classification["category"]
            repo = repo_map.get(repo_full_name)
            
            if repo:
                if category not in organized:
                    organized[category] = []
                organized[category].append(repo)
        
        return organized
    
    def execute_batch_operations(self, organized_repos: Dict[str, List[Dict]],
                               dry_run: bool = False) -> Dict[str, Dict]:
        """Execute batch star list operations"""
        results = {}
        
        for category, repos in organized_repos.items():
            if not repos:
                continue
            
            try:
                if dry_run:
                    results[category] = {
                        "success": True,
                        "action": "dry_run",
                        "repos_count": len(repos),
                        "repos": [repo["full_name"] for repo in repos]
                    }
                    logging.info(f"DRY RUN: Would create/update list '{category}' with {len(repos)} repos")
                else:
                    # Generate appropriate description
                    description = self._generate_list_description(category, repos)
                    result = self.create_or_update_list(category, description, repos)
                    results[category] = result
                    
            except Exception as e:
                logging.error(f"Failed to process category '{category}': {e}")
                results[category] = {"success": False, "error": str(e)}
        
        return results
    
    def set_summary_options(self, **options):
        """Set summary completion options"""
        self.summary_options.update(options)
    
    def generate_ai_summary(self, category: str, repos: List[Dict]) -> str:
        """Generate AI-powered summary for a star list"""
        if not self.summary_options.get("use_ai_summary", True):
            return self._generate_basic_description(category, repos)
        
        # Prepare repository information for AI
        repo_info = []
        for repo in repos[:5]:  # Use top 5 repos for analysis
            info = {
                "name": repo.get("name", ""),
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "topics": repo.get("topics", []),
                "stars": repo.get("stargazers_count", 0)
            }
            repo_info.append(info)
        
        prompt = f"""
Create a concise and informative description for a GitHub star list named "{category}".

Repository samples from this category:
{repo_info}

Total repositories in this category: {len(repos)}

Generate a description that:
1. Explains what this category contains
2. Highlights the main technologies/languages
3. Mentions the purpose or use case
4. Keeps it under 100 words
5. Sounds professional and helpful

Description:"""
        
        try:
            ai_description = call_llm_with_config(prompt, self.config)
            return ai_description.strip()
        except Exception as e:
            logging.warning(f"Failed to generate AI summary for {category}: {e}")
            return self._generate_basic_description(category, repos)
    
    def complete_list_summaries(self, existing_lists: List[Dict], repos_by_category: Dict[str, List[Dict]]) -> Dict[str, str]:
        """Complete or enhance summaries for star lists"""
        summaries = {}
        
        for category, repos in repos_by_category.items():
            existing_list = next((lst for lst in existing_lists if lst["name"] == category), None)
            
            if existing_list:
                existing_desc = existing_list.get("description", "")
                
                if not existing_desc and self.summary_options.get("auto_complete", True):
                    # Auto-complete missing description
                    summaries[category] = self.generate_ai_summary(category, repos)
                    logging.info(f"Auto-completed description for list: {category}")
                
                elif existing_desc and self.summary_options.get("enhance_existing", True):
                    # Enhance existing description
                    enhanced = self._enhance_existing_description(existing_desc, category, repos)
                    if enhanced != existing_desc:
                        summaries[category] = enhanced
                        logging.info(f"Enhanced description for list: {category}")
                    else:
                        summaries[category] = existing_desc
                else:
                    summaries[category] = existing_desc
            else:
                # New list - generate description
                summaries[category] = self.generate_ai_summary(category, repos)
        
        return summaries
    
    def _enhance_existing_description(self, existing_desc: str, category: str, repos: List[Dict]) -> str:
        """Enhance existing description with updated information"""
        if not self.summary_options.get("use_ai_summary", True):
            return existing_desc
        
        stats = self._get_repository_stats(repos)
        
        prompt = f"""
Enhance this existing GitHub star list description with updated information:

Current description: "{existing_desc}"
Category: {category}
Repository count: {len(repos)}
Repository statistics: {stats}

Enhance the description by:
1. Keeping the original tone and style
2. Adding relevant statistics if missing
3. Updating outdated information
4. Ensuring accuracy and completeness
5. Keeping it concise and professional

Enhanced description:"""
        
        try:
            enhanced = call_llm_with_config(prompt, self.config)
            return enhanced.strip()
        except Exception as e:
            logging.warning(f"Failed to enhance description for {category}: {e}")
            return existing_desc
    
    def _get_repository_stats(self, repos: List[Dict]) -> Dict:
        """Get statistics about repositories"""
        stats = {
            "count": len(repos),
            "languages": {},
            "total_stars": 0,
            "topics": {}
        }
        
        for repo in repos:
            # Language statistics
            lang = repo.get("language")
            if lang:
                stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
            
            # Star count
            stars = repo.get("stargazers_count", 0)
            stats["total_stars"] += stars
            
            # Topic statistics
            topics = repo.get("topics", [])
            for topic in topics:
                stats["topics"][topic] = stats["topics"].get(topic, 0) + 1
        
        # Get top languages and topics
        stats["top_languages"] = sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True)[:3]
        stats["top_topics"] = sorted(stats["topics"].items(), key=lambda x: x[1], reverse=True)[:5]
        
        return stats
    
    def _generate_basic_description(self, category: str, repos: List[Dict]) -> str:
        """Generate basic description without AI"""
        repo_count = len(repos)
        
        # Analyze main programming languages
        languages = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]
        lang_text = ", ".join([lang for lang, _ in top_languages])
        
        description = f"Auto-categorized {category} repositories ({repo_count} repos)"
        if lang_text:
            description += f" - Main languages: {lang_text}"
        
        if self.summary_options.get("include_stats", True):
            total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
            if total_stars > 0:
                description += f" - Total stars: {total_stars:,}"
        
        return description


def create_star_list_manager(github_client: GitHubClient, config: Dict = None) -> StarListManager:
    """Create StarListManager instance"""
    return StarListManager(github_client, config)


if __name__ == "__main__":
    # 测试star list管理器
    from utils.github_client import create_github_client
    
    try:
        client = create_github_client()
        manager = create_star_list_manager(client)
        
        # 获取现有lists
        existing_lists = manager.get_existing_lists()
        print(f"Found {len(existing_lists)} existing star lists")
        
        # 测试组织repos
        test_classification = {
            "user/repo1": {"category": "Web Development", "confidence": 0.9},
            "user/repo2": {"category": "Web Development", "confidence": 0.8},
            "user/repo3": {"category": "Data Science", "confidence": 0.95}
        }
        
        test_repos = [
            {"full_name": "user/repo1", "id": 1, "language": "JavaScript"},
            {"full_name": "user/repo2", "id": 2, "language": "TypeScript"},
            {"full_name": "user/repo3", "id": 3, "language": "Python"}
        ]
        
        organized = manager.organize_repos_by_category(test_classification, test_repos)
        print(f"Organized into {len(organized)} categories")
        
        # 执行dry run
        results = manager.execute_batch_operations(organized, dry_run=True)
        print("Dry run results:", results)
        
    except Exception as e:
        print(f"Error testing star list manager: {e}")