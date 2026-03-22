from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, ListView, ListItem
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel
import asyncio

from cli.commands import CommandHandler
from core.council import Council
from utils.models import AgentStatus

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
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_log", "Clear Log"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("ACTIVE AGENTS", classes="sidebar-title")
                yield ListView(id="agent-list")
            with Vertical(id="main-content"):
                yield Static("RESEARCH OUTPUT", classes="section-title")
                yield RichLog(id="output-log", highlight=True, markup=True)
                yield Static("SYSTEM LOGS", classes="section-title")
                yield RichLog(id="system-log", highlight=True, markup=True)
                yield Input(placeholder="Enter command (e.g., /council help)...", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self.council = Council(system_logger=self.system_log, research_logger=self.log_message)
        self.command_handler = CommandHandler(self, self.council)
        self.system_log("Welcome to [bold]THE COUNCIL[/] Multi-Agent AI Research Terminal.")
        self.system_log("Type [cyan]/council help[/cyan] for available commands.")
        # Refresh models on start
        asyncio.create_task(self.council.refresh_models())
        self.update_agent_list()

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
        """User-visible research output messages."""
        try:
            log = self.query_one("#output-log", RichLog)
            log.write(message)
        except:
            print(message)

    def system_log(self, message: str):
        """Technical background system logs."""
        try:
            log = self.query_one("#system-log", RichLog)
            log.write(message)
        except:
            print(f"[System] {message}")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return
        
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

if __name__ == "__main__":
    app = CouncilApp()
    app.run()
