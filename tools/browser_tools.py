<<<<<<< HEAD
import base64
import json
import subprocess


def _is_clipboard_write(args):
    """
    Return True when this Agent Browser command writes text
    to the browser clipboard.
    """

    return (
        isinstance(args, (list, tuple))
        and len(args) >= 3
        and str(args[0]) == "clipboard"
        and str(args[1]) == "write"
    )


def _clipboard_batch_payload(text):
    """
    Build Agent Browser batch JSON for one clipboard write.

    Using JSON over stdin avoids Windows CMD interpreting
    characters such as &, |, <, >, quotes, %, and ^.
    """

    return json.dumps(
        [
            [
                "clipboard",
                "write",
                str(text)
            ]
        ],
        ensure_ascii=False
    )


def _clipboard_command_text(text):
    """
    Build the command stored in the generated test script.

    Normal values keep the existing readable command:

        agent-browser clipboard write "Aya"

    Values that are unsafe to replay directly through Windows
    CMD are encoded and replayed through Agent Browser's
    batch --json stdin mode.

    The browser operation is still performed by Agent Browser.
    """

    text = str(text)

    cmd_sensitive_chars = (
        '&|<>^()%!"\r\n'
    )

    needs_safe_transport = any(
        char in text
        for char in cmd_sensitive_chars
    )

    if not needs_safe_transport:

        return (
            f'agent-browser clipboard write "{text}"'
        )

    payload = _clipboard_batch_payload(
        text
    )

    payload_b64 = base64.b64encode(
        payload.encode("utf-8")
    ).decode("ascii")

    return (
        'powershell -NoProfile -NonInteractive -Command '
        '"[Text.Encoding]::UTF8.GetString('
        "[Convert]::FromBase64String("
        f"'{payload_b64}'"
        '))" '
        '| agent-browser batch --json'
    )


def run_command(args, command_text=None):

=======
import subprocess


def run_command(args, command_text=None):
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """
    Execute Agent Browser CLI command.

    Returns:
        success
        output
        error
        command
    """

    try:

<<<<<<< HEAD
        # --------------------------------------------------
        # Clipboard write special handling
        #
        # Arbitrary exploratory input may contain Windows CMD
        # metacharacters such as:
        #
        #     & | < > " % ^
        #
        # Passing those values through shell=True as part of
        # one command string can change their meaning.
        #
        # Agent Browser supports batch --json via stdin, so
        # clipboard text is sent as JSON data instead of being
        # parsed by CMD.
        #
        # This changes only clipboard-write execution.
        # All other Agent Browser commands keep the existing
        # Windows-safe command construction below.
        # --------------------------------------------------

        if _is_clipboard_write(
            args
        ):

            payload = _clipboard_batch_payload(
                args[2]
            )

            result = subprocess.run(
                "agent-browser batch --json",
                input=payload,
                capture_output=True,
                text=True,
                shell=True,
                timeout=15
            )

        else:

            # --------------------------------------------------
            # Windows-safe command construction
            #
            # On Windows, agent-browser is commonly installed as
            # a .cmd launcher. Passing shell=True together with a
            # Python argument list can cause the subcommands/args
            # to be parsed incorrectly.
            #
            # Build one properly quoted command string instead.
            # --------------------------------------------------

            full_command = subprocess.list2cmdline(
                ["agent-browser"] + [
                    str(arg)
                    for arg in args
                ]
            )

            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                shell=True,
                timeout=15
            )
=======
        result = subprocess.run(
            ["agent-browser"] + args,
            capture_output=True,
            text=True,
            shell=True,
            timeout=15
        )
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

        if result.returncode == 0:

            return {
                "success": True,
                "output": result.stdout.strip(),
                "error": None,
                "command": command_text
            }

        else:

            return {
                "success": False,
                "output": None,
                "error": result.stderr.strip(),
                "command": command_text
            }

    except Exception as e:

        return {
            "success": False,
            "output": None,
            "error": str(e),
            "command": command_text
        }


def open_app(url):
<<<<<<< HEAD

=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """
    Open application using Agent Browser.
    """

    return run_command(
        ["open", url],
        f"agent-browser open {url}"
    )


def snapshot():
<<<<<<< HEAD

=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """
    Get current page accessibility snapshot.
    """

    return run_command(
        ["snapshot"],
        "agent-browser snapshot"
    )


<<<<<<< HEAD
def get_box(ref):

=======
def click(ref):
    """
    Click an element using its Agent Browser reference.
    """

    return run_command(
        ["click", ref],
        f"agent-browser click {ref}"
    )


def fill(ref, text):
    """
    Fill input field.
    """

    return run_command(
        ["fill", ref, text],
        f'agent-browser fill {ref} "{text}"'
    )


def get_box(ref):
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """
    Get the bounding box of an element.

    The bounding box contains:

        x
        y
        width
        height

    The ref should come from the current
    Agent Browser snapshot.

    Returns:
        success
        output
        error
        command
    """

    return run_command(
        ["get", "box", ref],
        f"agent-browser get box {ref}"
    )


<<<<<<< HEAD
def press(key):

    """
    Press a keyboard key or shortcut.

    Example:
        press("Control+a")

    Returns the real Agent Browser command so it can
    be included in the generated output script.
    """

    return run_command(
        [
            "press",
            key
        ],
        f"agent-browser press {key}"
    )


def click(ref):

    """
    Click an element using its CURRENT
    bounding-box coordinates.

    The ref is only used to dynamically
    retrieve the current element position.

    The generated browser command does NOT
    contain the ref.

    Instead it contains:

        mouse move x y
        mouse down left
        mouse up left

    This makes the generated test script
    coordinate-based instead of ref-based.
    """

    # --------------------------------------------------
    # 1. Get current element bounding box
    # --------------------------------------------------

    box_result = get_box(ref)

    if not box_result.get("success"):

        return {
            "success": False,
            "output": None,
            "error": box_result.get(
                "error",
                "Unable to get element bounding box."
            ),
            "command": None
        }

    # --------------------------------------------------
    # 2. Parse bounding box
    #
    # Expected output:
    #
    # x:      1071.609375
    # y:      163
    # width:  80.046875
    # height: 47
    # --------------------------------------------------

    try:

        box = {}

        for line in box_result.get(
            "output",
            ""
        ).splitlines():

            if ":" not in line:
                continue

            key, value = line.split(
                ":",
                1
            )

            box[key.strip()] = float(
                value.strip()
            )

        x = box["x"]
        y = box["y"]
        width = box["width"]
        height = box["height"]

    except (
        ValueError,
        KeyError
    ) as e:

        return {
            "success": False,
            "output": None,
            "error": (
                f"Invalid bounding box for "
                f"{ref}: {e}"
            ),
            "command": None
        }

    # --------------------------------------------------
    # 3. Calculate center of element
    #
    # Round to integer pixel coordinates because
    # Agent Browser mouse commands expect x/y positions.
    # --------------------------------------------------

    center_x = round(
        x + (width / 2)
    )

    center_y = round(
        y + (height / 2)
    )

    # --------------------------------------------------
    # 4. Move mouse to element center
    # --------------------------------------------------

    move_result = run_command(
        [
            "mouse",
            "move",
            str(center_x),
            str(center_y)
        ],
        (
            f"agent-browser mouse move "
            f"{center_x} {center_y}"
        )
    )

    if not move_result.get("success"):

        return move_result

    # --------------------------------------------------
    # 5. Press mouse button
    # --------------------------------------------------

    down_result = run_command(
        [
            "mouse",
            "down",
            "left"
        ],
        "agent-browser mouse down left"
    )

    if not down_result.get("success"):

        return down_result

    # --------------------------------------------------
    # 6. Release mouse button
    # --------------------------------------------------

    up_result = run_command(
        [
            "mouse",
            "up",
            "left"
        ],
        "agent-browser mouse up left"
    )

    if not up_result.get("success"):

        return up_result

    # --------------------------------------------------
    # 7. Build coordinate-based command
    # --------------------------------------------------

    command = "\n".join(
        [
            move_result["command"],
            down_result["command"],
            up_result["command"]
        ]
    )

    return {
        "success": True,
        "output": up_result.get(
            "output"
        ),
        "error": None,
        "command": command
    }


def fill(ref, text):

    """
    Fill an input using its CURRENT
    bounding-box coordinates.

    The ref is only used to dynamically
    retrieve the current element position.

    The generated browser commands use:

        mouse move
        mouse down
        mouse up
        press Control+a
        clipboard write
        clipboard paste

    The generated script therefore does
    not depend on a static element ref.
    """

    # --------------------------------------------------
    # 1. Get current element bounding box
    # --------------------------------------------------

    box_result = get_box(ref)

    if not box_result.get("success"):

        return {
            "success": False,
            "output": None,
            "error": box_result.get(
                "error",
                "Unable to get element bounding box."
            ),
            "command": None
        }

    # --------------------------------------------------
    # 2. Parse bounding box
    # --------------------------------------------------

    try:

        box = {}

        for line in box_result.get(
            "output",
            ""
        ).splitlines():

            if ":" not in line:
                continue

            key, value = line.split(
                ":",
                1
            )

            box[key.strip()] = float(
                value.strip()
            )

        x = box["x"]
        y = box["y"]
        width = box["width"]
        height = box["height"]

    except (
        ValueError,
        KeyError
    ) as e:

        return {
            "success": False,
            "output": None,
            "error": (
                f"Invalid bounding box for "
                f"{ref}: {e}"
            ),
            "command": None
        }

    # --------------------------------------------------
    # 3. Calculate center of element
    #
    # Round to integer pixel coordinates because
    # Agent Browser mouse commands expect x/y positions.
    # --------------------------------------------------

    center_x = round(
        x + (width / 2)
    )

    center_y = round(
        y + (height / 2)
    )

    # --------------------------------------------------
    # 4. Move mouse to input
    # --------------------------------------------------

    move_result = run_command(
        [
            "mouse",
            "move",
            str(center_x),
            str(center_y)
        ],
        (
            f"agent-browser mouse move "
            f"{center_x} {center_y}"
        )
    )

    if not move_result.get("success"):

        return move_result

    # --------------------------------------------------
    # 5. Click input
    # --------------------------------------------------

    down_result = run_command(
        [
            "mouse",
            "down",
            "left"
        ],
        "agent-browser mouse down left"
    )

    if not down_result.get("success"):

        return down_result

    up_result = run_command(
        [
            "mouse",
            "up",
            "left"
        ],
        "agent-browser mouse up left"
    )

    if not up_result.get("success"):

        return up_result

    # --------------------------------------------------
    # 6. Select any existing input value
    #
    # This makes fill() behave like a real fill action
    # instead of appending the new value to old text.
    # --------------------------------------------------

    select_all_result = press(
        "Control+a"
    )

    if not select_all_result.get("success"):

        return select_all_result

    # --------------------------------------------------
    # 7. Write value to clipboard
    #
    # run_command() sends clipboard text through
    # Agent Browser batch --json stdin so exploratory
    # special characters cannot be interpreted by CMD.
    # --------------------------------------------------

    clipboard_result = run_command(
        [
            "clipboard",
            "write",
            text
        ],
        _clipboard_command_text(
            text
        )
    )

    if not clipboard_result.get("success"):

        return clipboard_result

    # --------------------------------------------------
    # 8. Paste clipboard into input
    # --------------------------------------------------

    paste_result = run_command(
        [
            "clipboard",
            "paste"
        ],
        "agent-browser clipboard paste"
    )

    if not paste_result.get("success"):

        return paste_result

    # --------------------------------------------------
    # 9. Build coordinate + clipboard command
    # --------------------------------------------------

    command = "\n".join(
        [
            move_result["command"],
            down_result["command"],
            up_result["command"],
            select_all_result["command"],
            clipboard_result["command"],
            paste_result["command"]
        ]
    )

    return {
        "success": True,
        "output": paste_result.get(
            "output"
        ),
        "error": None,
        "command": command
    }


def navigate(url):

=======
def navigate(url):
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """
    Navigate to another URL.
    """

    return run_command(
        ["open", url],
        f"agent-browser open {url}"
    )


def screenshot(filename="screenshot.png"):
<<<<<<< HEAD

=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """
    Capture screenshot.
    """

    return run_command(
        ["screenshot", filename],
        f"agent-browser screenshot {filename}"
    )


<<<<<<< HEAD
def eval_js(script: str):

    """
    Run raw JavaScript in the page via agent-browser eval
    and return the raw stdout as output.
    """

    return run_command(
        ["eval", script],
        f"agent-browser eval {script[:80]}"
    )


def get_current_url():

    """
    Get the current page URL.
    """

    return run_command(
        ["get", "url"],
        "agent-browser get url"
    )


# --------------------------------------------------
# Used by Scenario 3's single-level, same-domain page discovery.
# Extracts real <a href> links from the live DOM (not guessed from
# the accessibility snapshot text), so the same-domain / depth-1
# filtering done in Python has accurate data to work with.
# --------------------------------------------------

_LIST_LINKS_SCRIPT = (
    "JSON.stringify(Array.from(document.querySelectorAll('a[href]'))"
    ".map(a => ({text: (a.textContent || '').trim().slice(0, 80), "
    "href: a.href})))"
)


def list_page_links():

    """
    Extract all <a href> links from the current page.
    """

    return eval_js(
        _LIST_LINKS_SCRIPT
    )


=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
if __name__ == "__main__":

    print("===== OPEN =====")

    print(
        open_app(
            "file:///C:/Users/PC/Downloads/agent browser/sample.html"
        )
    )

    print("===== SNAPSHOT =====")

    print(
        snapshot()
    )

    print("===== FILL NAME =====")

    print(
        fill(
            "@e2",
            "Aya"
        )
    )

    print("===== FILL EMAIL =====")

    print(
        fill(
            "@e3",
            "aya@example.com"
        )
    )

    print("===== FILL PASSWORD =====")

    print(
        fill(
            "@e4",
            "test1234"
        )
    )

    print("===== SCREENSHOT =====")

    print(
        screenshot(
            r"C:\Users\PC\Downloads\agent browser\test2.png"
        )
    )

<<<<<<< HEAD
    print("===== DONE =====")
=======
    print("===== DONE =====")
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
