import schedule
import time
import logging
import subprocess
import os
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Runs a python script and logs the output."""
    logger.info(f"🚀 Starting {script_name}...")
    try:
        # Resolve script path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, script_name)
        
        # Use the venv python if available, else system python
        # Check relative to script_dir (which is scripts/) -> ../venv
        venv_python = os.path.join(script_dir, '..', 'venv', 'bin', 'python')
        python_executable = venv_python if os.path.exists(venv_python) else "python3"
            
        result = subprocess.run(
            [python_executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"✅ {script_name} completed successfully.")
        # Log only a summary of output to avoid clutter
        output_lines = result.stdout.split('\n')
        last_lines = '\n'.join(output_lines[-5:]) if len(output_lines) > 5 else result.stdout
        logger.info(f"Output Summary:\n{last_lines}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {script_name} failed with error code {e.returncode}.")
        logger.error(f"Error Output:\n{e.stderr}")
    except Exception as e:
        logger.error(f"❌ Failed to run {script_name}: {e}")

def job_players():
    run_script("scraper_players.py")

def job_tactics():
    run_script("scraper_pipeline.py")

# Schedule Jobs
# Run daily in the early morning
schedule.every().day.at("02:00").do(job_players)
schedule.every().day.at("02:30").do(job_tactics)

logger.info("⏳ Scheduler started. Press Ctrl+C to stop.")
logger.info("📅 Scheduled jobs:")
logger.info("   - scraper_players.py at 02:00")
logger.info("   - scraper_pipeline.py at 02:30")

if __name__ == "__main__":
    # Run once immediately on startup to verify (Optional, but good for UX)
    # logger.info("Running initial sync...")
    # job_players()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
