import logging
import sys
import os
import click
from flow import create_qa_flow, create_star_classification_flow

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('star-tidy.log')
        ]
    )

def main_star_classification():
    """Main star classification functionality"""
    shared = {}
    
    try:
        # Create and run star classification flow
        star_flow = create_star_classification_flow()
        star_flow.run(shared)
        
        # Output final results
        if "operation_results" in shared:
            print("\n=== Star Classification Results ===")
            
            operation_results = shared["operation_results"]
            total_categories = len(operation_results)
            successful_ops = sum(1 for result in operation_results.values() 
                               if result.get("success", False))
            
            print(f"Total categories processed: {total_categories}")
            print(f"Successful operations: {successful_ops}")
            
            if shared.get("config", {}).get("dry_run", False):
                print("\n*** DRY RUN MODE - No actual changes made ***")
            
            print("\nCategory breakdown:")
            for category, result in operation_results.items():
                if result.get("success", False):
                    status = "✓" if not shared.get("config", {}).get("dry_run", False) else "⚠ (dry run)"
                    repo_count = result.get("repos_added", result.get("repos_count", 0))
                    action = result.get("action", "processed")
                    print(f"  {status} {category}: {repo_count} repos ({action})")
                else:
                    print(f"  ✗ {category}: Failed - {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logging.error(f"Star classification failed: {e}")
        print(f"Error: {e}")
        return False

def main_qa():
    """Legacy Q&A functionality"""
    shared = {
        "question": "In one sentence, what's the end of universe?",
        "answer": None
    }

    qa_flow = create_qa_flow()
    qa_flow.run(shared)
    print("Question:", shared["question"])
    print("Answer:", shared["answer"])

@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx, verbose, version):
    """GitHub Star Auto Classification Tool
    
    AI-powered tool to automatically classify GitHub starred repositories 
    into different star lists with smart summary completion.
    """
    if version:
        click.echo("Star Tidy v0.1.0")
        return
    
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)
    
    # If no subcommand is provided, run star classification
    if ctx.invoked_subcommand is None:
        ctx.invoke(star)


@cli.command()
@click.option("--mode", 
              type=click.Choice(["auto", "existing_lists"]), 
              default="auto",
              help="Classification mode: 'auto' creates new lists, 'existing_lists' uses current lists")
@click.option("--dry-run", is_flag=True, help="Run in dry-run mode (no actual changes)")
@click.option("--auto-complete-summaries/--no-auto-complete-summaries", 
              default=None,
              help="Auto-complete missing list descriptions")
@click.option("--enhance-existing-summaries/--no-enhance-existing-summaries",
              default=None, 
              help="Enhance existing list descriptions")
@click.option("--use-ai-summary/--no-use-ai-summary",
              default=None,
              help="Use AI to generate summaries")
@click.option("--include-stats/--no-include-stats",
              default=None,
              help="Include repository statistics in summaries")
@click.option("--exclude-repo", 
              multiple=True,
              help="Exclude specific repositories (can be used multiple times)")
@click.option("--config", 
              type=click.Path(exists=True),
              help="Path to configuration file")
@click.option("--ai-model",
              help="AI model to use (e.g., gpt-4o-mini, gpt-4)")
@click.option("--api-base",
              help="OpenAI API base URL for compatible services")
@click.option("--max-tokens",
              type=int,
              help="Maximum tokens to generate")
@click.option("--temperature",
              type=float,
              help="Sampling temperature (0-2)")
def star(mode, dry_run, auto_complete_summaries, enhance_existing_summaries, 
         use_ai_summary, include_stats, exclude_repo, config, ai_model, 
         api_base, max_tokens, temperature):
    """Run GitHub star classification"""
    
    # Set environment variables from CLI options
    if dry_run:
        os.environ["DRY_RUN"] = "true"
    
    os.environ["STAR_TIDY_MODE"] = mode
    
    # Set summary options if specified
    if auto_complete_summaries is not None:
        os.environ["AUTO_COMPLETE_SUMMARIES"] = str(auto_complete_summaries).lower()
    if enhance_existing_summaries is not None:
        os.environ["ENHANCE_EXISTING_SUMMARIES"] = str(enhance_existing_summaries).lower()
    if use_ai_summary is not None:
        os.environ["USE_AI_SUMMARY"] = str(use_ai_summary).lower()
    if include_stats is not None:
        os.environ["INCLUDE_STATS"] = str(include_stats).lower()
    
    # Set excluded repositories
    if exclude_repo:
        os.environ["EXCLUDE_REPOS"] = ",".join(exclude_repo)
    
    # Set config file path
    if config:
        os.environ["CONFIG_FILE"] = config
    
    # Set LLM options if specified
    if ai_model:
        os.environ["AI_MODEL"] = ai_model
    if api_base:
        os.environ["OPENAI_API_BASE"] = api_base
    if max_tokens:
        os.environ["MAX_TOKENS"] = str(max_tokens)
    if temperature is not None:
        os.environ["TEMPERATURE"] = str(temperature)
    
    # Display current settings
    click.echo(f"🚀 Starting star classification...")
    click.echo(f"Mode: {mode}")
    if dry_run:
        click.echo("⚠️  DRY RUN mode - no actual changes will be made")
    
    with click.progressbar(length=1, label="Running classification") as bar:
        success = main_star_classification()
        bar.update(1)
    
    if success:
        click.echo("✅ Classification completed successfully!")
        sys.exit(0)
    else:
        click.echo("❌ Classification failed!")
        sys.exit(1)


@cli.command()
def qa():
    """Run legacy Q&A functionality"""
    click.echo("Running legacy Q&A mode...")
    main_qa()


@cli.command()
def config():
    """Show current configuration"""
    from utils.config import load_config
    
    try:
        cfg = load_config()
        click.echo("📋 Current Configuration:")
        click.echo("=" * 40)
        
        config_dict = cfg.to_dict()
        for key, value in config_dict.items():
            if 'token' in key.lower() or 'key' in key.lower():
                display_value = f"{value[:8]}..." if value else "❌ Not set"
            elif value is None:
                display_value = "❌ Not set"
            else:
                display_value = value
            click.echo(f"{key:25}: {display_value}")
        
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--github-token", prompt=True, hide_input=True, help="GitHub Personal Access Token")
@click.option("--openai-key", prompt=True, hide_input=True, help="OpenAI API Key")
@click.option("--config-file", default="config.yaml", help="Configuration file to create")
def setup(github_token, openai_key, config_file):
    """Interactive setup wizard"""
    import yaml
    
    click.echo("🛠️  Setting up Star Tidy configuration...")
    
    # Basic configuration
    config_data = {
        "github_token": github_token,
        "openai_api_key": openai_key,
        "mode": "auto",
        "summary_options": {
            "auto_complete": True,
            "enhance_existing": True,
            "use_ai_summary": True,
            "include_stats": True
        },
        "exclude_repos": [],
        "dry_run": False
    }
    
    # Ask for additional options
    if click.confirm("Would you like to configure advanced options?"):
        api_base = click.prompt("OpenAI API Base URL", default="https://api.openai.com/v1")
        if api_base != "https://api.openai.com/v1":
            config_data["openai_api_base"] = api_base
        
        model = click.prompt("AI Model", default="gpt-4o-mini")
        if model != "gpt-4o-mini":
            config_data["ai_model"] = model
    
    # Write configuration file
    try:
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        click.echo(f"✅ Configuration saved to {config_file}")
        click.echo("🎉 Setup complete! You can now run: star-tidy star")
        
    except Exception as e:
        click.echo(f"❌ Failed to save configuration: {e}")
        sys.exit(1)


@cli.command()
def test():
    """Run system tests"""
    click.echo("🧪 Running system tests...")
    
    # Import and run test functions
    import subprocess
    try:
        result = subprocess.run([sys.executable, "test_system.py"], 
                              capture_output=True, text=True)
        click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("❌ test_system.py not found")
        sys.exit(1)


@cli.command("test-llm")
@click.option("--api-key", help="OpenAI API key (or use OPENAI_API_KEY env var)")
@click.option("--api-base", help="API base URL (or use OPENAI_API_BASE env var)")
@click.option("--model", help="Model name (or use AI_MODEL env var)")
def test_llm(api_key, api_base, model):
    """Test LLM connection and configuration"""
    from utils.call_llm import test_llm_connection, call_llm
    
    click.echo("🔮 Testing LLM connection...")
    
    # Show current configuration
    actual_api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    actual_model = model or os.environ.get("AI_MODEL", "gpt-4o-mini")
    actual_api_key = api_key or os.environ.get("OPENAI_API_KEY")
    
    click.echo(f"API Base: {actual_api_base}")
    click.echo(f"Model: {actual_model}")
    click.echo(f"API Key: {'✅ Set' if actual_api_key else '❌ Not set'}")
    
    if not actual_api_key:
        click.echo("❌ No API key provided. Set OPENAI_API_KEY or use --api-key")
        sys.exit(1)
    
    # Test connection
    click.echo("\n🔍 Testing connection...")
    success = test_llm_connection(
        api_key=actual_api_key,
        base_url=actual_api_base,
        model=actual_model
    )
    
    if success:
        click.echo("✅ LLM connection successful!")
        
        # Test actual call
        click.echo("\n💬 Testing actual LLM call...")
        try:
            response = call_llm(
                prompt="Respond with 'Test successful' if you can read this.",
                api_key=actual_api_key,
                base_url=actual_api_base,
                model=actual_model,
                max_tokens=20
            )
            click.echo(f"Response: {response}")
            click.echo("🎉 LLM test completed successfully!")
        except Exception as e:
            click.echo(f"❌ LLM call failed: {e}")
            sys.exit(1)
    else:
        click.echo("❌ LLM connection failed!")
        sys.exit(1)


def main():
    """Entry point for the CLI"""
    cli()

if __name__ == "__main__":
    main()
