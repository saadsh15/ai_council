from textual.app import App, ComposeResult
from textual.widgets import RichLog
from rich.markdown import Markdown

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield RichLog(id="log", markup=True)

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("Standard text")
        log.write("[bold red]Rich Markup[/bold red]")
        log.write(Markdown("# Markdown Header\nThis is **bold** and *italic*."))
        # Also test if we can write multiple lines as one Markdown object
        log.write(Markdown("## Subheader\n- List item 1\n- List item 2"))

if __name__ == "__main__":
    # We can't easily run TUI in this environment and see output, 
    # but we can check if it crashes or has issues.
    # Actually, I'll just check the code of RichLog if possible or assume it works based on Rich compatibility.
    print("Script created. I will try to run it briefly to check for crashes.")
