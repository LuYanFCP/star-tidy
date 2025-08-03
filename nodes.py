from pocketflow import Node, BatchNode
import logging
from typing import Dict, List, Any

from utils.config import load_config
from utils.github_client import create_github_client
from utils.repo_analyzer import analyze_repository
from utils.star_list_manager import create_star_list_manager

class InitializeNode(Node):
    """Initialize configuration and validate API credentials"""
    
    def prep(self, shared):
        # Load configuration from environment variables or config file
        config = load_config()
        return config
    
    def exec(self, config):
        # Validate configuration
        config.validate()
        
        # Test GitHub API connection
        github_client = create_github_client(config.get("github_token"))
        user_info = github_client.get_user_info()
        
        logging.info(f"Successfully authenticated as GitHub user: {user_info['login']}")
        
        return {
            "config": config.to_dict(),
            "github_client": github_client,
            "user_info": user_info
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["config"] = exec_res["config"]
        shared["github_client"] = exec_res["github_client"]
        shared["user_info"] = exec_res["user_info"]
        
        logging.info("Configuration initialized successfully")
        return "default"

class FetchStarredReposNode(Node):
    """Fetch user's starred repositories"""
    
    def prep(self, shared):
        github_client = shared["github_client"]
        return github_client
    
    def exec(self, github_client):
        # Fetch starred repositories
        starred_repos = github_client.get_starred_repos()
        logging.info(f"Fetched {len(starred_repos)} starred repositories")
        return starred_repos
    
    def post(self, shared, prep_res, exec_res):
        shared["starred_repos"] = exec_res
        return "default"

class ModeDecisionNode(Node):
    """Decide processing mode and fetch existing star lists if needed"""
    
    def prep(self, shared):
        config = shared["config"]
        github_client = shared["github_client"]
        return config["mode"], github_client
    
    def exec(self, inputs):
        mode, github_client = inputs
        
        if mode == "existing_lists":
            # Fetch existing star lists
            star_list_manager = create_star_list_manager(github_client)
            existing_lists = star_list_manager.get_existing_lists()
            
            logging.info(f"Found {len(existing_lists)} existing star lists")
            
            return {
                "mode": mode,
                "existing_lists": existing_lists,
                "existing_categories": [lst["name"] for lst in existing_lists]
            }
        else:
            return {
                "mode": "auto",
                "existing_lists": [],
                "existing_categories": []
            }
    
    def post(self, shared, prep_res, exec_res):
        shared["mode"] = exec_res["mode"]
        shared["existing_lists"] = exec_res["existing_lists"]
        shared["existing_categories"] = exec_res["existing_categories"]
        
        logging.info(f"Operating in {exec_res['mode']} mode")
        return "default"

class AnalyzeRepositoriesNode(BatchNode):
    """Use AI to analyze and classify each repository"""
    
    def prep(self, shared):
        starred_repos = shared["starred_repos"]
        config = shared["config"]
        existing_categories = shared.get("existing_categories", [])
        mode = shared.get("mode", "auto")
        
        # Filter out excluded repositories
        exclude_repos = config.get("exclude_repos", [])
        filtered_repos = []
        
        for repo in starred_repos:
            if repo["full_name"] not in exclude_repos:
                # Include necessary context information for each repo
                filtered_repos.append((repo, existing_categories, mode, config))
        
        logging.info(f"Analyzing {len(filtered_repos)} repositories (excluded {len(starred_repos) - len(filtered_repos)})")
        return filtered_repos
    
    def exec(self, repo_data):
        # repo_data is a tuple of (repo, existing_categories, mode, config)
        repo, existing_categories, mode, config = repo_data
        
        # Use AI to analyze repository
        try:
            result = analyze_repository(repo, existing_categories, mode, config)
            logging.info(f"Analyzed {repo['full_name']}: {result['category']} (confidence: {result['confidence']:.2f})")
            return repo["full_name"], result
        except Exception as e:
            logging.error(f"Failed to analyze {repo['full_name']}: {e}")
            return repo["full_name"], {
                "category": "Uncategorized",
                "reason": f"Analysis failed: {str(e)}",
                "confidence": 0.1
            }
    
    def post(self, shared, prep_res, exec_res_list):
        # Organize analysis results as dictionary
        classification_results = {}
        for repo_name, result in exec_res_list:
            classification_results[repo_name] = result
        
        shared["classification_results"] = classification_results
        
        # Count classification results
        categories = {}
        for result in classification_results.values():
            category = result["category"]
            categories[category] = categories.get(category, 0) + 1
        
        logging.info(f"Classification complete. Categories: {categories}")
        return "default"

class ManageStarListsNode(Node):
    """Create or update star lists based on classification results"""
    
    def prep(self, shared):
        github_client = shared["github_client"]
        classification_results = shared["classification_results"]
        starred_repos = shared["starred_repos"]
        config = shared["config"]
        
        return {
            "github_client": github_client,
            "classification_results": classification_results,
            "starred_repos": starred_repos,
            "dry_run": config.get("dry_run", False),
            "config": config
        }
    
    def exec(self, inputs):
        github_client = inputs["github_client"]
        classification_results = inputs["classification_results"]
        starred_repos = inputs["starred_repos"]
        dry_run = inputs["dry_run"]
        config = inputs.get("config", {})
        
        # Create star list manager with config
        star_list_manager = create_star_list_manager(github_client, config)
        
        # Configure summary options
        summary_options = config.get("summary_options", {})
        if summary_options:
            star_list_manager.set_summary_options(**summary_options)
        
        # Get existing lists for summary completion
        existing_lists = star_list_manager.get_existing_lists()
        
        # Organize repositories based on classification results
        organized_repos = star_list_manager.organize_repos_by_category(
            classification_results, starred_repos
        )
        
        # Complete/enhance list summaries
        enhanced_summaries = star_list_manager.complete_list_summaries(
            existing_lists, organized_repos
        )
        
        # Execute batch operations with enhanced summaries
        results = {}
        for category, repos in organized_repos.items():
            if not repos:
                continue
                
            enhanced_description = enhanced_summaries.get(category, "")
            
            if dry_run:
                results[category] = {
                    "success": True,
                    "action": "dry_run",
                    "repos_count": len(repos),
                    "repos": [repo["full_name"] for repo in repos],
                    "enhanced_description": enhanced_description
                }
                logging.info(f"DRY RUN: Would create/update list '{category}' with {len(repos)} repos")
                logging.info(f"Enhanced description: {enhanced_description}")
            else:
                try:
                    result = star_list_manager.create_or_update_list(
                        category, enhanced_description, repos
                    )
                    result["enhanced_description"] = enhanced_description
                    results[category] = result
                except Exception as e:
                    logging.error(f"Failed to process category '{category}': {e}")
                    results[category] = {"success": False, "error": str(e)}
        
        return {
            "organized_repos": organized_repos,
            "operation_results": results,
            "enhanced_summaries": enhanced_summaries
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["organized_repos"] = exec_res["organized_repos"]
        shared["operation_results"] = exec_res["operation_results"]
        
        # Generate summary report
        total_repos = sum(len(repos) for repos in exec_res["organized_repos"].values())
        total_categories = len(exec_res["organized_repos"])
        successful_operations = sum(1 for result in exec_res["operation_results"].values() 
                                  if result.get("success", False))
        
        logging.info(f"Star list management complete:")
        logging.info(f"  - Total repositories processed: {total_repos}")
        logging.info(f"  - Categories created/updated: {total_categories}")
        logging.info(f"  - Successful operations: {successful_operations}/{total_categories}")
        
        return "default"

# Legacy nodes for backward compatibility
class GetQuestionNode(Node):
    def exec(self, _):
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        shared["question"] = exec_res
        return "default"

class AnswerNode(Node):
    def prep(self, shared):
        return shared["question"]
    
    def exec(self, question):
        from utils.call_llm import call_llm
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res