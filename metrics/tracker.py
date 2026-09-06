import time
import os


class MetricsLogger:

    def __init__(self):
        self.start_time = time.time()

        self.node_execution_times = {}

        self.prompt_tokens = 0
        self.output_tokens = 0

        self.screenshot_count = 0
        self.screenshot_total_size_kb = 0

        # --------------------------------------------------
        # Detailed metrics for every node
        # --------------------------------------------------

        self.node_metrics = {}

    def reset(self):
        self.start_time = time.time()

        self.node_execution_times = {}

        self.prompt_tokens = 0
        self.output_tokens = 0

        self.screenshot_count = 0
        self.screenshot_total_size_kb = 0

        self.node_metrics = {}

    def log_node_time(
        self,
        node_name: str,
        duration: float
    ):
        self.node_execution_times[node_name] = (
            self.node_execution_times.get(
                node_name,
                0
            )
            + duration
        )

    def log_tokens(
        self,
        prompt_tokens: int,
        output_tokens: int
    ):
        self.prompt_tokens += prompt_tokens
        self.output_tokens += output_tokens

    def log_model_call(
        self,
        node_name: str,
        model_name: str,
        model_type: str,
        duration: float,
        prompt_tokens: int,
        output_tokens: int,
        prompt_chars: int,
        prompt_words: int,
        image_size_kb: float = 0
    ):
        """
        Record detailed metrics for one LLM/VLM call.

        In addition to node totals, this stores the metrics
        for every individual model call.
        """

        # --------------------------------------------------
        # Update global totals
        # --------------------------------------------------

        self.prompt_tokens += prompt_tokens
        self.output_tokens += output_tokens

        # --------------------------------------------------
        # Create node entry if it doesn't exist
        # --------------------------------------------------

        if node_name not in self.node_metrics:

            self.node_metrics[node_name] = {
                "calls": 0,
                "llm_calls": 0,
                "vlm_calls": 0,

                "time_sec": 0,

                "prompt_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,

                "prompt_chars": 0,
                "prompt_words": 0,

                "image_count": 0,
                "image_total_size_kb": 0,

                # --------------------------------------------------
                # NEW:
                # Store every individual model call
                # --------------------------------------------------

                "call_details": []
            }

        metrics = self.node_metrics[node_name]

        # --------------------------------------------------
        # General call information
        # --------------------------------------------------

        metrics["calls"] += 1

        metrics["time_sec"] += duration

        # --------------------------------------------------
        # Model type
        # --------------------------------------------------

        if model_type == "LLM":
            metrics["llm_calls"] += 1

        elif model_type == "VLM":
            metrics["vlm_calls"] += 1

        # --------------------------------------------------
        # Token information
        # --------------------------------------------------

        total_tokens = (
            prompt_tokens
            + output_tokens
        )

        metrics["prompt_tokens"] += prompt_tokens

        metrics["output_tokens"] += output_tokens

        metrics["total_tokens"] += total_tokens

        # --------------------------------------------------
        # Prompt size information
        # --------------------------------------------------

        metrics["prompt_chars"] += prompt_chars

        metrics["prompt_words"] += prompt_words

        # --------------------------------------------------
        # Image information
        # --------------------------------------------------

        if model_type == "VLM":

            metrics["image_count"] += 1

            metrics["image_total_size_kb"] += (
                image_size_kb
            )

        # --------------------------------------------------
        # NEW:
        # Save metrics for THIS individual call
        # --------------------------------------------------

        call_number = len(
            metrics["call_details"]
        ) + 1

        metrics["call_details"].append(
            {
                "call": call_number,

                "model_name": model_name,

                "model_type": model_type,

                "duration_sec": round(
                    duration,
                    2
                ),

                "prompt_tokens": prompt_tokens,

                "output_tokens": output_tokens,

                "total_tokens": total_tokens,

                "prompt_chars": prompt_chars,

                "prompt_words": prompt_words,

                "image_size_kb": round(
                    image_size_kb,
                    2
                )
            }
        )

    def log_screenshot(
        self,
        screenshot_path: str
    ):
        if not os.path.exists(screenshot_path):
            return

        size_bytes = os.path.getsize(
            screenshot_path
        )

        size_kb = size_bytes / 1024

        self.screenshot_count += 1

        self.screenshot_total_size_kb += size_kb

    def get_summary(self):

        rounded_node_times = {
            node_name: round(duration, 2)
            for node_name, duration
            in self.node_execution_times.items()
        }

        # --------------------------------------------------
        # Prepare detailed node metrics
        # --------------------------------------------------

        detailed_node_metrics = {}

        for node_name, metrics in self.node_metrics.items():

            detailed_node_metrics[node_name] = {
                "calls": metrics["calls"],

                "llm_calls": metrics["llm_calls"],

                "vlm_calls": metrics["vlm_calls"],

                "time_sec": round(
                    metrics["time_sec"],
                    2
                ),

                "prompt_tokens": (
                    metrics["prompt_tokens"]
                ),

                "output_tokens": (
                    metrics["output_tokens"]
                ),

                "total_tokens": (
                    metrics["total_tokens"]
                ),

                "prompt_chars": (
                    metrics["prompt_chars"]
                ),

                "prompt_words": (
                    metrics["prompt_words"]
                ),

                "image_count": (
                    metrics["image_count"]
                ),

                "image_total_size_kb": round(
                    metrics["image_total_size_kb"],
                    2
                ),

                # --------------------------------------------------
                # NEW:
                # Return individual call metrics
                # --------------------------------------------------

                "call_details": metrics[
                    "call_details"
                ]
            }

        return {
            "total_run_time_sec": round(
                time.time() - self.start_time,
                2
            ),

            "node_times": rounded_node_times,

            "prompt_tokens": self.prompt_tokens,

            "output_tokens": self.output_tokens,

            "total_tokens": (
                self.prompt_tokens
                + self.output_tokens
            ),

            "screenshots": {
                "count": self.screenshot_count,

                "total_size_kb": round(
                    self.screenshot_total_size_kb,
                    2
                )
            },

            "node_metrics": detailed_node_metrics
        }


metrics_logger = MetricsLogger()


def print_metrics_report(metrics):

    print(
        "\n==================== METRICS REPORT ===================="
    )

    print(
        f"Total Run Time        : "
        f"{metrics['total_run_time_sec']} seconds"
    )

    print(
        f"Prompt Tokens         : "
        f"{metrics['prompt_tokens']}"
    )

    print(
        f"Output Tokens         : "
        f"{metrics['output_tokens']}"
    )

    print(
        f"Total Tokens          : "
        f"{metrics['total_tokens']}"
    )

    print(
        f"Screenshots Count     : "
        f"{metrics['screenshots']['count']}"
    )

    print(
        f"Screenshots Total Size: "
        f"{metrics['screenshots']['total_size_kb']} KB"
    )

    # --------------------------------------------------
    # Node execution times
    # --------------------------------------------------

    print("\nNode Execution Times:")

    for node_name, duration in metrics["node_times"].items():

        print(
            f"  {node_name}: "
            f"{duration} seconds"
        )

    # --------------------------------------------------
    # Detailed model metrics
    # --------------------------------------------------

    print(
        "\n==================== NODE MODEL METRICS ===================="
    )

    for node_name, node in metrics["node_metrics"].items():

        print(
            f"\n[{node_name}]"
        )

        print(
            f"  Calls              : "
            f"{node['calls']}"
        )

        print(
            f"  LLM Calls          : "
            f"{node['llm_calls']}"
        )

        print(
            f"  VLM Calls          : "
            f"{node['vlm_calls']}"
        )

        print(
            f"  Model Time         : "
            f"{node['time_sec']} seconds"
        )

        print(
            f"  Prompt Tokens      : "
            f"{node['prompt_tokens']}"
        )

        print(
            f"  Output Tokens      : "
            f"{node['output_tokens']}"
        )

        print(
            f"  Total Tokens       : "
            f"{node['total_tokens']}"
        )

        print(
            f"  Prompt Characters  : "
            f"{node['prompt_chars']}"
        )

        print(
            f"  Prompt Words       : "
            f"{node['prompt_words']}"
        )

        if node["image_count"] > 0:

            print(
                f"  Images             : "
                f"{node['image_count']}"
            )

            print(
                f"  Image Size         : "
                f"{node['image_total_size_kb']} KB"
            )

        # --------------------------------------------------
        # NEW:
        # Individual model call metrics
        # --------------------------------------------------

        if node["call_details"]:

            print(
                "\n  Call Details:"
            )

            for call in node["call_details"]:

                print(
                    f"    Call {call['call']}: "
                    f"Prompt {call['prompt_tokens']} | "
                    f"Output {call['output_tokens']} | "
                    f"Total {call['total_tokens']} | "
                    f"Time {call['duration_sec']}s"
                )

    print(
        "\n============================================================\n"
    )