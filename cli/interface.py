from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, ListView, ListItem
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
import asyncio

from cli.commands import CommandHandler
from core.council import Council
from utils.models import AgentStatus

class VerticalResizer(Static):
    """A vertical bar that can be dragged left/right to resize the sidebar."""
    start_x: Optional[int] = None
    start_width: Optional[int] = None

    def render(self) -> str:
        return "\n".join(["⋮"] * self.size.height)

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.capture_mouse()
        self.start_x = event.screen_x
        self.start_width = self.app.query_one("#sidebar").size.width

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if event.button == 1 and self.start_x is not None: # Left mouse button
            delta = event.screen_x - self.start_x
            new_width = self.start_width + delta
            if new_width >= 10:
                self.app.query_one("#sidebar").styles.width = new_width

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.release_mouse()
        self.start_x = None

class HorizontalResizer(Static):
    """A horizontal bar that can be dragged up/down to resize log panels."""
    start_y: Optional[int] = None
    start_height: Optional[int] = None

    def render(self) -> str:
        return "⋯" * self.size.width

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.capture_mouse()
        self.start_y = event.screen_y
        self.start_height = self.app.query_one("#output-log").size.height

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if event.button == 1 and self.start_y is not None: # Left mouse button
            delta = event.screen_y - self.start_y
            new_height = self.start_height + delta
            if new_height >= 3:
                self.app.query_one("#output-log").styles.height = new_height

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.release_mouse()
        self.start_y = None

class AgentStatusWidget(Static):
    def __init__(self, agent_id: str, status: str, **kwargs):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.status = status

    def render(self) -> Panel:
        color = "green" if self.status == "active" else "red"
        # Handle string or enum
        status_str = self.status.value if hasattr(self.status, "value") else str(self.status)
        return Panel(f"[{color}]{self.agent_id}[/]\n{status_str.upper()}", title="Agent", padding=(0, 1))

import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

class CouncilApp(App):
    TITLE = "THE COUNCIL - AI Research Terminal"
    CSS_PATH = get_resource_path("cli/styles.tcss")
    BINDINGS = [
        Binding("ctrl+c", "request_quit", "Quit"),
        Binding("ctrl+l", "clear_log", "Clear Log"),
        Binding("ctrl+t", "cycle_theme", "Theme", show=False),
        Binding("ctrl+y", "copy_research", "Copy Recent"),
        Binding("ctrl+k", "copy_system", "Copy System"),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
    ]

    _exit_requested = False
    _research_buffer = []
    _system_buffer = []
    _command_history = []
    _history_index = -1

    def on_key(self, event: events.Key) -> None:
        """Handle arrow keys for command history."""
        if self.query_one("#command-input").has_focus:
            if event.key == "up":
                if self._command_history:
                    if self._history_index == -1:
                        self._history_index = len(self._command_history) - 1
                    elif self._history_index > 0:
                        self._history_index -= 1
                    
                    self.query_one("#command-input").value = self._command_history[self._history_index]
                    event.prevent_default()
            elif event.key == "down":
                if self._command_history:
                    if self._history_index != -1:
                        if self._history_index < len(self._command_history) - 1:
                            self._history_index += 1
                            self.query_one("#command-input").value = self._command_history[self._history_index]
                        else:
                            self._history_index = -1
                            self.query_one("#command-input").value = ""
                        event.prevent_default()

    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        resizer = self.query_one("#sidebar-resizer")
        sidebar.display = not sidebar.display
        resizer.display = not resizer.display

    def action_copy_research(self) -> None:
        """Copy the most recent research final consensus to clipboard."""
        # Try to get from current session first
        if self.council.current_session and self.council.current_session.final_consensus:
            content = self.council.current_session.final_consensus
        else:
            # Fallback to buffer if no current session consensus
            content = "\n".join(self._research_buffer)
            
        if content:
            self.copy_to_clipboard(content)
            self.notify("Most recent research copied to clipboard!", timeout=2)
        else:
            self.notify("No research output to copy.", severity="warning")

    def action_copy_system(self) -> None:
        """Copy the system logs to clipboard."""
        content = "\n".join(self._system_buffer)
        if content:
            self.copy_to_clipboard(content)
            self.notify("System logs copied to clipboard!", timeout=2)
        else:
            self.notify("System log is empty.", severity="warning")

    def action_cycle_theme(self) -> None:
        """Cycle through available color palettes and save preference."""
        themes = ["default", "cyberpunk", "nord", "dracula"]
        current = self.council.config.palette
        try:
            next_index = (themes.index(current) + 1) % len(themes)
        except ValueError:
            next_index = 0
        
        new_theme = themes[next_index]
        self.council.config.palette = new_theme
        
        from storage.config import save_config
        save_config(self.council.config)
        
        self.set_palette(new_theme)
        self.notify(f"Theme changed to: {new_theme.capitalize()}", timeout=2)

    def action_request_quit(self) -> None:
        """Handle Ctrl+C with a confirmation requirement."""
        if self._exit_requested:
            self.exit()
        else:
            self._exit_requested = True
            self.notify("Press Ctrl+C again to exit the app", timeout=3)
            self.set_timer(3, self.reset_exit_request)

    def reset_exit_request(self) -> None:
        """Reset the exit request flag."""
        self._exit_requested = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("ACTIVE AGENTS", classes="sidebar-title")
                yield ListView(id="agent-list")
            yield VerticalResizer(id="sidebar-resizer")
            with Vertical(id="main-content"):
                yield Static("RESEARCH OUTPUT", classes="section-title")
                yield RichLog(id="output-log", highlight=True, markup=True)
                yield HorizontalResizer(id="log-resizer")
                yield Static("SYSTEM LOGS", classes="section-title")
                yield RichLog(id="system-log", highlight=True, markup=True)
                yield Input(placeholder="Enter command (e.g., /council help)...", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self.council = Council(system_logger=self.system_log, research_logger=self.log_message)
        self.command_handler = CommandHandler(self, self.council)
        # Apply initial palette
        self.set_palette(self.council.config.palette)
        
        self.system_log("Welcome to [bold]THE COUNCIL[/] Multi-Agent AI Research Terminal.")
        self.system_log("Type [cyan]/council help[/cyan] for available commands.")
        # Refresh models on start
        asyncio.create_task(self.council.refresh_models())
        self.update_agent_list()

    def set_palette(self, palette_name: str):
        """Update the app theme based on palette name."""
        # Remove any existing palette classes
        for cls in list(self.classes):
            if cls.startswith("palette-"):
                self.remove_class(cls)
        # Add the new one
        self.add_class(f"palette-{palette_name}")

    def update_agent_list(self):
        """Sync the sidebar with active council agents."""
        try:
            agent_list = self.query_one("#agent-list", ListView)
            agent_list.clear()
            for agent in self.council.list_agents():
                agent_list.append(ListItem(AgentStatusWidget(agent.agent_id, agent.status)))
        except:
            pass

    def log_message(self, message: str):
        """User-visible research output messages with markdown support."""
        self._research_buffer.append(message)
        try:
            log = self.query_one("#output-log", RichLog)
            # 1. If it contains Rich closing tags, it's definitely Rich markup
            if "[/]" in message or "[bold" in message or "[cyan" in message:
                # But wait, if it also has MD indicators, MD might be better?
                # Usually command echoes don't have MD.
                if not any(ind in message for ind in ["**", "###", "```"]):
                    log.write(message)
                    return

            # 2. Check for Markdown indicators
            md_indicators = ["**", "* ", "# ", " - ", "```", "---"]
            if any(ind in message for ind in md_indicators) or "\n" in message:
                log.write(Markdown(message))
            elif "[" in message and "]" in message and "(" in message: # Likely a MD link
                log.write(Markdown(message))
            elif "[" in message and "]" in message: # Likely Rich or a citation
                log.write(message)
            else:
                log.write(Markdown(message))
        except:
            print(message)

    def system_log(self, message: str):
        """Technical background system logs with markdown support."""
        self._system_buffer.append(message)
        try:
            log = self.query_one("#system-log", RichLog)
            if "[" in message and "]" in message and "**" not in message:
                log.write(message)
            else:
                log.write(Markdown(message))
        except:
            print(f"[System] {message}")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return
        
        # Add to history
        if not self._command_history or self._command_history[-1] != command:
            self._command_history.append(command)
        self._history_index = -1
        
        event.input.value = ""
        self.log_message(f"> [bold cyan]{command}[/]")
        
        # Process command
        result = await self.command_handler.execute(command)
        if result.success:
            self.log_message(result.message)
        else:
            self.log_message(f"[red]{result.message}[/]")
            
        # Refresh sidebar in case agents were added/removed/eliminated
        self.update_agent_list()

    def action_clear_log(self) -> None:
        self.query_one("#output-log", RichLog).clear()
        self.query_one("#system-log", RichLog).clear()
        self._research_buffer.clear()
        self._system_buffer.clear()

if __name__ == "__main__":
    app = CouncilApp()
    app.run()
