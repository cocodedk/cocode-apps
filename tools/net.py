"""The only code that touches the network. Tests never call it."""
import http.client
import urllib.error
import urllib.request

AGENT = "cocode-apps-audit/0.1 (+https://github.com/cocodedk/cocode-apps)"


def fetch(url: str, timeout: float = 20.0) -> tuple[int, str]:
    """Return (status, text); (0, "") when there is no answer, whatever the reason. Never raises."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(400_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, ""
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException, ValueError):
        return 0, ""
