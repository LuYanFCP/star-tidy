import logging
from typing import Dict, List, Optional
from utils.call_llm import call_llm_with_config

class RepositoryAnalyzer:
    """Use AI to analyze repositories for classification"""
    
    def __init__(self, existing_categories: List[str] = None, config: Dict = None):
        self.existing_categories = existing_categories or []
        self.config = config or {}
        
    def analyze_repository(self, repo_info: Dict, mode: str = "auto") -> Dict:
        """分析单个repository并返回分类结果"""
        
        # 提取repository信息
        name = repo_info.get("name", "")
        description = repo_info.get("description", "")
        language = repo_info.get("language", "")
        topics = repo_info.get("topics", [])
        readme_content = repo_info.get("readme", "")  # 如果有的话
        
        # 构建分析提示
        if mode == "existing_lists" and self.existing_categories:
            prompt = self._build_existing_categories_prompt(
                name, description, language, topics, readme_content
            )
        else:
            prompt = self._build_auto_categorization_prompt(
                name, description, language, topics, readme_content
            )
        
        try:
            response = call_llm_with_config(prompt, self.config)
            return self._parse_ai_response(response)
        except Exception as e:
            logging.error(f"Failed to analyze repository {name}: {e}")
            return {
                "category": "Uncategorized",
                "reason": f"Analysis failed: {str(e)}",
                "confidence": 0.1
            }
    
    def _build_auto_categorization_prompt(self, name: str, description: str, 
                                        language: str, topics: List[str], 
                                        readme: str = "") -> str:
        """构建自动分类的提示"""
        
        prompt = f"""
Please analyze this GitHub repository and classify it into an appropriate category.

Repository Information:
- Name: {name}
- Description: {description or "No description provided"}
- Primary Language: {language or "Not specified"}
- Topics: {', '.join(topics) if topics else "None"}

Analysis Guidelines:
1. Consider the repository's primary purpose and technology stack
2. Choose from these common categories or suggest a new one:
   - Web Development
   - Mobile Development  
   - Data Science & ML
   - DevOps & Infrastructure
   - UI/UX & Design
   - Backend & APIs
   - Frontend Frameworks
   - Database & Storage
   - Security & Privacy
   - Game Development
   - Programming Languages
   - Development Tools
   - Documentation & Learning
   - Open Source Libraries
   - System Programming
   - Cloud & Serverless

3. If none of the above categories fit well, suggest a specific category name

Please respond in YAML format:
```yaml
category: "Category Name"
reason: "Brief explanation for this categorization"
confidence: 0.9
```

The confidence should be between 0.0 and 1.0, where 1.0 means very confident.
"""
        return prompt
    
    def _build_existing_categories_prompt(self, name: str, description: str,
                                        language: str, topics: List[str],
                                        readme: str = "") -> str:
        """构建基于已有分类的提示"""
        
        categories_list = '\n'.join([f"  - {cat}" for cat in self.existing_categories])
        
        prompt = f"""
Please analyze this GitHub repository and classify it into one of the existing star list categories.

Repository Information:
- Name: {name}
- Description: {description or "No description provided"}
- Primary Language: {language or "Not specified"}
- Topics: {', '.join(topics) if topics else "None"}

Existing Star List Categories:
{categories_list}

Instructions:
1. Choose the MOST appropriate category from the existing list above
2. If the repository doesn't fit any existing category well, choose "Uncategorized"
3. Provide a clear reason for your choice

Please respond in YAML format:
```yaml
category: "Exact Category Name from the list above"
reason: "Brief explanation for this categorization"
confidence: 0.9
```

The confidence should be between 0.0 and 1.0, where 1.0 means very confident.
"""
        return prompt
    
    def _parse_ai_response(self, response: str) -> Dict:
        """解析AI的响应"""
        try:
            import yaml
            
            # 提取YAML部分
            if "```yaml" in response:
                yaml_part = response.split("```yaml")[1].split("```")[0].strip()
            elif "```" in response:
                yaml_part = response.split("```")[1].split("```")[0].strip()
            else:
                yaml_part = response.strip()
            
            result = yaml.safe_load(yaml_part)
            
            # 验证必需字段
            if not isinstance(result, dict):
                raise ValueError("Response is not a valid dictionary")
            
            if "category" not in result:
                raise ValueError("Missing 'category' field")
            
            # 设置默认值
            return {
                "category": result["category"],
                "reason": result.get("reason", "No reason provided"),
                "confidence": float(result.get("confidence", 0.5))
            }
            
        except Exception as e:
            logging.error(f"Failed to parse AI response: {e}")
            return {
                "category": "Uncategorized",
                "reason": f"Failed to parse AI response: {str(e)}",
                "confidence": 0.1
            }


def analyze_repository(repo_info: Dict, existing_categories: List[str] = None, 
                      mode: str = "auto", config: Dict = None) -> Dict:
    """Convenience function to analyze repository"""
    analyzer = RepositoryAnalyzer(existing_categories, config)
    return analyzer.analyze_repository(repo_info, mode)


if __name__ == "__main__":
    # 测试repository分析
    test_repo = {
        "name": "react",
        "description": "A declarative, efficient, and flexible JavaScript library for building user interfaces.",
        "language": "JavaScript",
        "topics": ["javascript", "react", "frontend", "ui"]
    }
    
    result = analyze_repository(test_repo)
    print("Analysis result:")
    print(f"Category: {result['category']}")
    print(f"Reason: {result['reason']}")
    print(f"Confidence: {result['confidence']}")