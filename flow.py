from pocketflow import Flow
from nodes import (
    GetQuestionNode, AnswerNode,  # Legacy nodes
    InitializeNode, FetchStarredReposNode, ModeDecisionNode,
    AnalyzeRepositoriesNode, ManageStarListsNode
)

def create_qa_flow():
    """Create and return a question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    answer_node = AnswerNode()
    
    # Connect nodes in sequence
    get_question_node >> answer_node
    
    # Create flow starting with input node
    return Flow(start=get_question_node)

def create_star_classification_flow():
    """Create and return the main star classification flow."""
    # Create all nodes
    initialize_node = InitializeNode()
    fetch_repos_node = FetchStarredReposNode()
    mode_decision_node = ModeDecisionNode()
    analyze_repos_node = AnalyzeRepositoriesNode()
    manage_lists_node = ManageStarListsNode()
    
    # Connect nodes in sequence
    initialize_node >> fetch_repos_node
    fetch_repos_node >> mode_decision_node
    mode_decision_node >> analyze_repos_node
    analyze_repos_node >> manage_lists_node
    
    # Create flow starting with initialization
    return Flow(start=initialize_node)

# Default flows
qa_flow = create_qa_flow()
star_flow = create_star_classification_flow()