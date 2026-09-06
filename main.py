import argparse

from graph import build_graph
from tools.browser_tools import open_app
from metrics.tracker import (
    metrics_logger,
    print_metrics_report
)


def run_scenario1(
    requirement: str,
    app_path: str
) -> dict:

    metrics_logger.reset()

    print("Opening application...")

    open_result = open_app(app_path)

    if not open_result.get("success"):
        raise RuntimeError(
            f"Failed to open application: {open_result.get('error')}"
        )

    print("Application opened successfully.")

    graph = build_graph()

    initial_state = {
        "requirement": requirement,
        "app_path": app_path,
        "retry_count": 0,
        "browser_commands": [
            open_result.get("command")
        ]
    }

    final_state = graph.invoke(initial_state)

    metrics = metrics_logger.get_summary()

    final_state["_metrics"] = metrics

    return final_state



def run_scenario2(
    existing_script: str,
    app_path: str
) -> dict:

    metrics_logger.reset()

    print("Opening updated application...")

    open_result = open_app(app_path)

    if not open_result.get("success"):
        raise RuntimeError(
            f"Failed to open application: {open_result.get('error')}"
        )

    print("Updated application opened successfully.")

    graph = build_graph()

    initial_state = {
        "existing_script": existing_script,
        "app_path": app_path,
        "retry_count": 0,
        "browser_commands": [
            open_result.get("command")
        ]
    }

    final_state = graph.invoke(initial_state)

    metrics = metrics_logger.get_summary()

    final_state["_metrics"] = metrics

    return final_state


def run_scenario3(
    app_path: str,
    max_pages: int = 3
) -> dict:
    """
    Scenario 3: Exploratory Testing / Autonomous Bug Discovery.

    No requirement and no existing script — the agent explores the
    application on its own, proposing and executing edge-case
    scenarios, then reporting verdicts per case.
    """

    metrics_logger.reset()

    print("Opening application for exploratory testing...")

    open_result = open_app(app_path)

    if not open_result.get("success"):
        raise RuntimeError(
            f"Failed to open application: {open_result.get('error')}"
        )

    print("Application opened successfully.")

    graph = build_graph()

    initial_state = {
        "app_path": app_path,
        "retry_count": 0,
        "max_pages": max_pages,
        "visited_pages": [app_path],
        "current_page_url": app_path,
        "pages_queue": [],
        "pages_discovered": False,
        "has_next_page": False,
        "case_validations": [],
        "browser_commands": [
            open_result.get("command")
        ]
    }

    final_state = graph.invoke(initial_state)

    metrics = metrics_logger.get_summary()

    final_state["_metrics"] = metrics

    return final_state



def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run Scenario 1 (new test), "
            "Scenario 2 (maintenance), or "
            "Scenario 3 (exploratory testing)."
        )
    )


    parser.add_argument(
        "--requirement",
        required=False,
        help="Testing requirement for Scenario 1"
    )


    parser.add_argument(
        "--existing_script",
        required=False,
        help="Existing test script for Scenario 2 (inline string)"
    )


    parser.add_argument(
        "--existing_script_file",
        required=False,
        help=(
            "Path to a file containing the existing test script "
            "for Scenario 2 (alternative to --existing_script)"
        )
    )


    parser.add_argument(
        "--app_path",
        required=True,
        help="URL or path of application under test"
    )


    parser.add_argument(
        "--max_pages",
        type=int,
        default=3,
        required=False,
        help=(
            "Maximum number of pages to explore in "
            "Scenario 3 (default: 3, max: 4)"
        )
    )


    args = parser.parse_args()


    # --------------------------------------------------
    # Resolve existing_script from file if provided
    # --------------------------------------------------

    existing_script = args.existing_script

    if (
        not existing_script
        and args.existing_script_file
    ):
        try:
            with open(
                args.existing_script_file,
                "r",
                encoding="utf-8"
            ) as f:
                existing_script = f.read().strip()

            if not existing_script:
                print(
                    f"\nWarning: --existing_script_file "
                    f"'{args.existing_script_file}' is empty."
                )
        except FileNotFoundError:
            print(
                f"\nError: file not found: "
                f"{args.existing_script_file}"
            )
            return
        except Exception as e:
            print(
                f"\nError reading --existing_script_file: {e}"
            )
            return


    # --------------------------------------------------
    # Route to the correct scenario
    # --------------------------------------------------

    if existing_script:

        print("\n=== Scenario 2: Test Script Maintenance ===")
        print(f"App Path: {args.app_path}\n")

        try:

            result = run_scenario2(
                existing_script,
                args.app_path
            )

        except Exception as e:

            print("\nAgent execution failed:")
            print(e)
            return


    elif args.requirement:

        print("\n=== Scenario 1 ===")
        print(f"Requirement: {args.requirement}")
        print(f"App Path: {args.app_path}\n")


        try:

            result = run_scenario1(
                args.requirement,
                args.app_path
            )

        except Exception as e:

            print("\nAgent execution failed:")
            print(e)
            return


    else:

        print("\n=== Scenario 3: Exploratory Testing ===")
        print(f"App Path: {args.app_path}")
        print(f"Max Pages: {args.max_pages}\n")

        try:

            result = run_scenario3(
                args.app_path,
                args.max_pages
            )

        except Exception as e:

            print("\nAgent execution failed:")
            print(e)
            return



    if "_metrics" in result:

        print_metrics_report(
            result["_metrics"]
        )


    print("\n=== Final State ===")


    for key, value in result.items():

        if key not in [
            "_metrics",
            "generated_output"
        ]:

            print(
                f"{key}: {value}"
            )


    print("\n=== Generated Test Script ===")


    print(
        result.get(
            "generated_output",
            "No test script generated."
        )
    )



if __name__ == "__main__":
    main()