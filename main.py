import argparse
import sys
from src.shared.utils.logger import get_logger

logger = get_logger("main")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RPA Runner")
    
    parser.add_argument(
        "--bot",
        nargs="+",
        choices=["crm", "logistics", "all", "crm-attach"],
        default=["crm"],
        help="Which bot(s) to run",
    )

    return parser


def run_crm():
    from src.crm.crm_bot import run_crm_bot
    run_crm_bot()


def run_crm_attach():
    from src.crm.crm_bot import run_crm_attach_bot
    run_crm_attach_bot()


def run_logistics():
    from src.logistics.nbs_bot import NBSBot
    bot = NBSBot()
    bot.run()


def main():
    parser = build_parser()
    args = parser.parse_args()

    logger.info(f"Starting RPA — bot: {args.bot}")
    try:

        if "all" in args.bot or "crm" in args.bot:
            run_crm()

        if "all" in args.bot or "logistics" in args.bot:
            run_logistics()

        if "all" in args.bot or "crm-attach" in args.bot:
            run_crm_attach()

        
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
