import subprocess

def run_command(args):
    
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
                "error": None
            }
        else:
            return {
                "success": False,
                "output": None,
                "error": result.stderr.strip()
            }

    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": str(e)
        }


def open_app(url):
    return run_command(["open", url])


def snapshot():
    return run_command(["snapshot"])


def click(ref):
    return run_command(["click", ref])


def fill(ref, text):
    return run_command(["fill", ref, text])


def navigate(url):
    return run_command(["open", url])


def screenshot(filename="screenshot.png"):
    return run_command(["screenshot", filename])


if __name__ == "__main__":
    print("===== OPEN =====")
    print(open_app("file:///C:/Users/PC/Downloads/agent browser/sample.html"))

    print("===== SNAPSHOT =====")
    print(snapshot())

    print("===== FILL NAME =====")
    print(fill("@e2", "Aya"))

    print("===== FILL EMAIL =====")
    print(fill("@e3", "aya@example.com"))

    print("===== FILL PASSWORD =====")
    print(fill("@e4", "test1234"))

    print("===== SCREENSHOT =====")
    print(screenshot(r"C:\Users\PC\Downloads\agent browser\test2.png"))

    print("===== DONE =====")