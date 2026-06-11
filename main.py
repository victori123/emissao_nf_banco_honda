"""
RPA main entry point.
Usage:
    python main.py --bot crm
    python main.py --bot logistics
    python main.py --bot all
"""
import argparse
import sys
from src.shared.utils.logger import get_logger

logger = get_logger("main")

def run_crm():
    from src.crm.crm_bot import run_crm_bot
    run_crm_bot()

def run_logistics():
    # Will be implemented in the next phase
    logger.info("Logistics bot not yet implemented.")

def main():
    parser = argparse.ArgumentParser(description="RPA Runner")
    parser.add_argument(
        "--bot",
        choices=["crm", "logistics", "all"],
        default="crm",
        help="Which bot to run (default: crm)",
    )
    args = parser.parse_args()

    logger.info(f"Starting RPA — bot: {args.bot}")
    try:
        if args.bot in ("crm", "all"):
            run_crm()
        if args.bot in ("logistics", "all"):
            run_logistics()
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
