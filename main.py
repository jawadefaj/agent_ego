import sys
import os
import asyncio
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Add current path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import browser-use and other required modules
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from langchain_deepseek import ChatDeepSeek

# Load environment variables
load_dotenv()

os.environ["DEEPSEEK_API_KEY"] = "sk-"
os.environ["OPENAI_API_KEY"] = "sk-proj"




# Configuration loading
def load_config(config_path: str):
    """Load configuration from yaml file"""
    import yaml
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {str(e)}")

# Configure logging with more detailed settings
def setup_logging():
    # Create a formatter that includes timestamp, level, and module name
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # File handler for persistent logs
    file_handler = logging.FileHandler(log_dir / 'agent_debug.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('playwright').setLevel(logging.DEBUG)
    
    # Ensure our app's loggers are set to DEBUG
    logging.getLogger('browser_use').setLevel(logging.DEBUG)
    
    return root_logger

# Setup logging
logger = setup_logging()

# Load configuration
config_path = "config.yaml"
config = load_config(config_path)

print(config)
# Extract configurations
browser_config = config['browser']
chat_llm_config = config['agent']['chat']
reasoning_llm_config = config['agent']['reasoning']
vision_llm_config = config['agent']['vision']

# Ensure the folder for saving conversations exists
save_conversation_path = r"C:\Users\abjaw\OneDrive\Documents\GitHub\agent_ego\conversations"
os.makedirs(save_conversation_path, exist_ok=True)

async def test_browser():
    """Simple function to test if the browser works properly"""
    logger.info("Starting browser test")
    browser = None
    context = None
    
    try:
        # Initialize browser with simple configuration
        logger.debug("Creating browser configuration")
        b_config = BrowserConfig(
            headless=False,  # Make it visible to see what's happening
            disable_security=True
        )
        
        logger.debug("Initializing browser")
        browser = Browser()
        
        # Create a browser context and try to navigate to a simple website
        logger.info("Creating browser context")
        context = await browser.new_context()
        
        logger.debug(f"Browser context created: {context}")
        
        # Navigate to a website
        logger.info("Navigating to reddit.com")
        await context.navigate_to("https://www.reddit.com")
        
        # Wait a bit to see if it loaded
        logger.info("Waiting for page to load...")
        await asyncio.sleep(5)
        
        # Get the page title
        state = await context.get_state()
        logger.info(f"Page title: {state.title}")
        logger.info(f"Current URL: {state.url}")
        
        logger.info("Browser test completed successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Browser test failed: {str(e)}")
        return False
    finally:
        # Clean up resources
        if context:
            logger.info("Closing browser context")
            await context.close()
        if browser:
            logger.info("Closing browser")
            await browser.close()

async def create_agent_with_task(task: str, browser: Browser, browser_context: Optional[BrowserContext] = None):
    """Create an agent with the specified task and browser settings"""
    try:
        # Initialize LLM
        logger.debug(f"Initializing LLM with model: {chat_llm_config['model']}")
        chat_llm = ChatDeepSeek(
            model=chat_llm_config["model"],
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            temperature=chat_llm_config["temperature"],
            max_tokens=chat_llm_config["max_tokens"],
            timeout=30,
            max_retries=3,
        )
        reasoning_llm = ChatDeepSeek(
            model=reasoning_llm_config["model"],
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            temperature=reasoning_llm_config["temperature"],
            max_tokens=reasoning_llm_config["max_tokens"],
            timeout=30,
            max_retries=3,
        )
        vision_llm = ChatDeepSeek(
            model=vision_llm_config["model"],
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=vision_llm_config["temperature"],
            max_tokens=vision_llm_config["max_tokens"],
            timeout=30,
            max_retries=3,
        )
        
        # Initialize Agent
        logger.debug("-----------------Creating agent instance with context --------------------")
        context = await browser.new_context()
        agent = Agent(
            task=task,
            llm=chat_llm,
            browser=browser,  # Use the passed browser instance
            use_vision=True,
            use_vision_for_planner=True,
            save_conversation_path=r"C:\Users\abjaw\OneDrive\Documents\GitHub\agent_ego\conversations",
            max_actions_per_step=5,
            generate_gif=True,
            planner_llm=vision_llm,
        )
        
        # # Navigate to the initial page
        # logger.info("Navigating to initial page")
        # await context.navigate_to("https://www.reddit.com")
        
        return agent
    except Exception as e:
        logger.exception(f"Failed to create agent: {str(e)}")
        raise

async def main():
    logger.info("Starting the application")
    
    # First test if the browser works
    # browser_works = await test_browser()
    # if not browser_works:
    #     logger.error("Browser test failed, cannot continue with agent")
    #     return
    # exit()
    print("=" * 50)
    browser = None
    browser_context = None
    
    try:
        # Initialize browser with properly fixed config
        logger.debug("Creating browser configuration for agent")
        b_config = BrowserConfig(
            # headless=browser_config.get('headless', False),
            # disable_security=browser_config.get('disable_security', True),
            # chrome_instance_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            
        )
        
        context_config = BrowserContextConfig(
            highlight_elements=True,
            viewport_expansion=100,  # Show more elements to the agent
            wait_between_actions=1.0,  # Give a bit more time between actions
            # save_downloads_path=r"C:\Users\abjaw\OneDrive\Documents\GitHub\agent_ego\downloads"  # Save any downloads here
        )
        
        logger.debug("Initializing browser for agent")
        browser = Browser(b_config)
        
        logger.info(browser)
        
        # Define the task for the agent
        task = "Go to Reddit, search for 'browser-use', click on the first post and return the first comment."
        
        # Create and run the agent
        agent = await create_agent_with_task(task, browser)
        
        # Run Agent
        logger.info("Running agent...")
        result = await agent.run(max_steps=3)  # Limit to 20 steps maximum
        print("=" * 50)
        print(result)
        logger.info("Agent execution completed")
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
    except Exception as e:
        logger.exception(f"An error occurred during execution: {str(e)}")
    finally:
        # Clean up resources in reverse order
        if browser_context:
            logger.info("Closing browser context")
            try:
                await browser_context.close()
            except Exception as e:
                logger.error(f"Error closing browser context: {str(e)}")
        
        if browser:
            logger.info("Closing browser")
            try:
                await browser.close()
                logger.info("Browser resources cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during browser cleanup: {str(e)}")

def run_async_main():
    """Helper function to properly set up and run the async main function"""
    logger.info("Application starting")
    
    # Windows-specific configuration
    if sys.platform == "win32":
        logger.debug("Using ProactorEventLoop for Windows")
        try:
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        except Exception as e:
            logger.error(f"Failed to set ProactorEventLoop: {e}")
            exit()
            # Fallback to the policy approach
            # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    run_async_main()