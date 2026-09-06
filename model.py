import re
import time
import inspect
import os

from PIL import Image

from metrics.tracker import metrics_logger


# ==================================================
# Backend selection based on GEMINI_API_KEY
#
# If GEMINI_API_KEY is set  → Gemini API
# If GEMINI_API_KEY is unset → Ollama (Qwen2.5-VL)
#
# The rest of the codebase calls invoke_llm / invoke_vlm
# without knowing which backend is active.
# ==================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

USE_GEMINI = bool(GEMINI_API_KEY)

if USE_GEMINI:
    from google import genai
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "gemini-2.5-flash"
    print(f"[model] Using Gemini API (model: {MODEL_NAME})")
else:
    import ollama
    _gemini_client = None
    MODEL_NAME = "qwen2.5vl:7b"
    print(f"[model] Using Ollama (model: {MODEL_NAME})")


# ==================================================
# Per-node detection (BASE's existing approach)
# ==================================================

def _detect_node_name() -> str:
    """
    Detect which agent node called the LLM/VLM function.

    This allows us to measure token usage per node
    without changing the node logic.
    """

    node_functions = {
        "understand_task": "understand",
        "create_plan": "plan",
        "analyze_ui_with_vlm": "observe",
        "observe_ui": "observe",
        "_validate_case_with_vlm": "observe",
        "_validate_final_result": "generate",
        "decide_action": "decide",
        "reflect_replan": "reflect",
        "verify_behavior": "verify",
        "generate_output": "generate"
    }

    for frame_info in inspect.stack():
        function_name = frame_info.function

        if function_name in node_functions:
            return node_functions[function_name]

    return "unknown"


# ==================================================
# Gemini rate limiting (SOURCE's approach)
# ==================================================

# The free tier allows 15 requests/minute.
# 60 / 15 = 4s minimum spacing — we add a small buffer.

_MIN_SECONDS_BETWEEN_CALLS = 4.5
_MAX_RETRIES = 5
_last_call_time = 0.0


def _wait_for_rate_limit():
    """
    Block just long enough to keep our own call rate under the
    free-tier limit, so we avoid triggering 429s in the first place.
    """

    global _last_call_time

    elapsed = time.monotonic() - _last_call_time

    if elapsed < _MIN_SECONDS_BETWEEN_CALLS:
        time.sleep(_MIN_SECONDS_BETWEEN_CALLS - elapsed)

    _last_call_time = time.monotonic()


def _extract_retry_delay(
    error_message: str,
    default: float = 10.0
) -> float:
    """
    Gemini's error message often includes e.g. "retry in 8.8s" —
    use that exact delay when available, with a small buffer.
    """

    match = re.search(
        r"retry in ([\d.]+)s",
        error_message,
        re.IGNORECASE
    )

    if match:
        return float(match.group(1)) + 1.0

    return default


def _generate_with_retry(contents):
    """
    Call Gemini generate_content with automatic retry on rate-limit
    (429) or transient-unavailable (503) errors.
    """

    last_error = None

    for attempt in range(_MAX_RETRIES):

        _wait_for_rate_limit()

        try:
            return _gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=contents
            )

        except Exception as e:
            message = str(e)
            last_error = e

            is_rate_limited = (
                "RESOURCE_EXHAUSTED" in message
                or "429" in message
            )
            is_unavailable = (
                "UNAVAILABLE" in message
                or "503" in message
            )

            if (
                (is_rate_limited or is_unavailable)
                and attempt < _MAX_RETRIES - 1
            ):
                delay = _extract_retry_delay(message)

                reason = (
                    "rate limit"
                    if is_rate_limited
                    else "temporarily unavailable"
                )

                print(
                    f"Model call {reason}, retrying in "
                    f"{delay:.1f}s "
                    f"(attempt {attempt + 1}/{_MAX_RETRIES})..."
                )

                time.sleep(delay)
                continue

            raise

    raise last_error


# ==================================================
# invoke_llm — text-only prompt
# ==================================================

def invoke_llm(prompt: str) -> str:
    """
    Send a text prompt to the active model backend
    and record detailed metrics.
    """

    node_name = _detect_node_name()

    start_time = time.time()

    if USE_GEMINI:
        # ----- Gemini path -----
        response = _generate_with_retry(prompt)
        duration = time.time() - start_time

        usage = response.usage_metadata
        prompt_tokens = (
            getattr(usage, "prompt_token_count", 0)
            if usage else 0
        )
        output_tokens = (
            getattr(usage, "candidates_token_count", 0)
            if usage else 0
        )

        result_text = response.text

    else:
        # ----- Ollama path -----
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        duration = time.time() - start_time

        prompt_tokens = (
            getattr(response, "prompt_eval_count", 0) or 0
        )
        output_tokens = (
            getattr(response, "eval_count", 0) or 0
        )

        result_text = response.message.content

    # --------------------------------------------------
    # Log detailed node metrics
    # --------------------------------------------------

    metrics_logger.log_model_call(
        node_name=node_name,
        model_name=MODEL_NAME,
        model_type="LLM",
        duration=duration,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        prompt_chars=len(prompt),
        prompt_words=len(prompt.split())
    )

    return result_text


# ==================================================
# invoke_vlm — prompt + screenshot
# ==================================================

def invoke_vlm(prompt: str, image_path: str) -> str:
    """
    Send a prompt + screenshot to the active model backend
    and record detailed metrics.
    """

    node_name = _detect_node_name()

    # Validate image opens correctly
    image = Image.open(image_path)

    # --------------------------------------------------
    # Get image information
    # --------------------------------------------------

    image_size_kb = 0

    if os.path.exists(image_path):
        image_size_kb = (
            os.path.getsize(image_path) / 1024
        )

    start_time = time.time()

    if USE_GEMINI:
        # ----- Gemini path -----
        response = _generate_with_retry([
            prompt,
            image
        ])

        duration = time.time() - start_time

        usage = response.usage_metadata
        prompt_tokens = (
            getattr(usage, "prompt_token_count", 0)
            if usage else 0
        )
        output_tokens = (
            getattr(usage, "candidates_token_count", 0)
            if usage else 0
        )

        result_text = response.text

    else:
        # ----- Ollama path -----
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_path]
                }
            ]
        )

        duration = time.time() - start_time

        prompt_tokens = (
            getattr(response, "prompt_eval_count", 0) or 0
        )
        output_tokens = (
            getattr(response, "eval_count", 0) or 0
        )

        result_text = response.message.content

    # --------------------------------------------------
    # Log detailed node metrics
    # --------------------------------------------------

    metrics_logger.log_model_call(
        node_name=node_name,
        model_name=MODEL_NAME,
        model_type="VLM",
        duration=duration,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        prompt_chars=len(prompt),
        prompt_words=len(prompt.split()),
        image_size_kb=image_size_kb
    )

    return result_text