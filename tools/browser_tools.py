import subprocess


def run_command(args, command_text=None):
    """
    Execute Agent Browser CLI command.

    Returns:
        success
        output
        error
        command
    """

    try:

        result = subprocess.run(
            ["agent-browser"] + args,
            capture_output=True,
            text=True,
            shell=True,
            timeout=15
        )

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
    """
    Open application using Agent Browser.
    """

    return run_command(
        ["open", url],
        f"agent-browser open {url}"
    )


def snapshot():
    """
    Get current page accessibility snapshot.
    """

    return run_command(
        ["snapshot"],
        "agent-browser snapshot"
    )


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


def navigate(url):
    """
    Navigate to another URL.
    """

    return run_command(
        ["open", url],
        f"agent-browser open {url}"
    )


def screenshot(filename="screenshot.png"):
    """
    Capture screenshot.
    """

    return run_command(
        ["screenshot", filename],
        f"agent-browser screenshot {filename}"
    )

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

    return eval_js(_LIST_LINKS_SCRIPT)


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

    print("===== DONE =====")