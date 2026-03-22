import shlex
import asyncio
from typing import List, Optional, Callable
from pydantic import BaseModel
from core.council import Council

class CommandResult(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class CommandHandler:
    def __init__(self, app, council: Council):
        self.app = app
        self.council = council
        self.commands = {
            "/council help": self.handle_help,
            "/council start": self.handle_start,
            "/council begin": self.handle_begin,
            "/council add": self.handle_add,
            "/council remove": self.handle_remove,
            "/council list": self.handle_list,
            "/council research": self.handle_research,
            "/council config": self.handle_config,
            "/council preferences": self.handle_preferences,
            "/council history": self.handle_history,
            "/council clear": self.handle_clear,
            "/council toggle": self.handle_toggle,
            "/quit": self.handle_quit,
        }

    async def execute(self, command_line: str) -> CommandResult:
        parts = shlex.split(command_line)
        if not parts:
            return CommandResult(success=False, message="Empty command")

        cmd_prefix = None
        for i in range(len(parts), 0, -1):
            potential_prefix = " ".join(parts[:i])
            if potential_prefix in self.commands:
                cmd_prefix = potential_prefix
                args = parts[i:]
                break
        
        if cmd_prefix:
            return await self.commands[cmd_prefix](args)
        else:
            return CommandResult(success=False, message=f"Unknown command: {command_line}")

    async def handle_help(self, args: List[str]) -> CommandResult:
        help_text = """
[bold yellow]Available Commands:[/bold yellow]
/council start - Initialize the council with default agents
/council begin <query> - Start a deliberative council meeting (agents talk to each other)
/council add <provider> [model] - Add an agent
/council remove <agent_id> - Remove an agent
/council list - List all agents
/council preferences <text> - Set global research tailoring preferences
/council toggle - Toggle active agents sidebar (Shortcut: Ctrl+B)
/council research <query> - Begin standard research (consensus via elimination)
/council config - View/modify configuration (e.g., /council config prompt <text>)
/council history - View history
/council clear - Clear current session
/quit - Exit
"""
        return CommandResult(success=True, message=help_text)

    async def handle_preferences(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /council preferences <text>")
        
        value = " ".join(args)
        from storage.config import save_config
        self.council.config.user_preferences = value
        save_config(self.council.config)
        return CommandResult(success=True, message=f"Updated User Preferences to: [cyan]{value}[/]")

    async def handle_begin(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /council begin <query>")
        query = " ".join(args)
        asyncio.create_task(self.council.run_deliberation(query))
        return CommandResult(success=True, message=f"Council meeting convened for: [cyan]{query}[/]")

    async def handle_start(self, args: List[str]) -> CommandResult:
        # Re-fetch models just in case
        await self.council.refresh_models()
        
        if not self.council.available_ollama_models:
            return CommandResult(success=False, message="No Ollama models found. Please download one using 'ollama pull <model>'.")

        # Clear existing agents to start fresh
        self.council.agents = []
        
        # Add agents for the first 3 unique models available
        models_to_add = [m.name for m in self.council.available_ollama_models[:3]]
        
        # Ensure we have at least 2 agents (even if it's the same model twice)
        if len(models_to_add) == 1:
            models_to_add.append(models_to_add[0])
            
        for model in models_to_add:
            self.council.add_agent("ollama", model)
            
        return CommandResult(success=True, message=f"Council initialized with {len(self.council.agents)} agents using models: {', '.join(models_to_add)}")

    async def handle_add(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /council add <provider> [model]")
        provider = args[0]
        model = args[1] if len(args) > 1 else None
        
        if provider == "ollama":
            available = [m.name for m in self.council.available_ollama_models]
            if model and model not in available:
                return CommandResult(success=False, message=f"Model '{model}' not found in Ollama. Available: {', '.join(available[:5])}...")
        
        try:
            agent_id = self.council.add_agent(provider, model)
            return CommandResult(success=True, message=f"Added agent: {agent_id}")
        except Exception as e:
            return CommandResult(success=False, message=str(e))

    async def handle_remove(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /council remove <agent_id>")
        self.council.remove_agent(args[0])
        return CommandResult(success=True, message=f"Removed agent: {args[0]}")

    async def handle_list(self, args: List[str]) -> CommandResult:
        # Agents in Council
        agents = self.council.list_agents()
        msg = ""
        
        if agents:
            msg += "[bold yellow]Active Agents in Council:[/bold yellow]\n"
            for a in agents:
                status_color = "green" if a.status == "active" else "red"
                msg += f"- {a.agent_id} ({a.provider}:{a.model}) [[{status_color}]{a.status}[/]]\n"
            msg += "\n"
        else:
            msg += "[yellow]No agents currently in the council.[/]\n\n"
        
        # Available Models
        if self.council.available_ollama_models:
            msg += "[bold cyan]Available Ollama Models:[/bold cyan]\n"
            for m in self.council.available_ollama_models:
                is_default = "*" if m.name == self.council.config.default_model else " "
                size_gb = m.size / 1e9
                msg += f"{is_default} - {m.name} ({size_gb:.2f} GB)\n"
            msg += "\n[dim]* = Current default model[/]"
        else:
            msg += "[red]No Ollama models found locally.[/]"
            
        return CommandResult(success=True, message=msg)

    async def handle_research(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, message="Usage: /council research <query>")
        query = " ".join(args)
        # We don't await run_research here because we want the TUI to stay responsive
        # and Council will log to the output-log directly.
        # But for now, let's await it to keep it simple, or use a background task.
        asyncio.create_task(self.council.run_research(query))
        return CommandResult(success=True, message=f"Research started for: [cyan]{query}[/]")

    async def handle_vote(self, args: List[str]) -> CommandResult:
        return CommandResult(success=True, message="Manual voting not fully implemented yet.")

    async def handle_eliminate(self, args: List[str]) -> CommandResult:
        return CommandResult(success=True, message="Manual elimination not fully implemented yet.")

    async def handle_export(self, args: List[str]) -> CommandResult:
        return CommandResult(success=True, message="Export not implemented yet.")

    async def handle_config(self, args: List[str]) -> CommandResult:
        if not args:
            config = self.council.config
            msg = "[bold yellow]Current Configuration:[/bold yellow]\n"
            msg += f"Default Provider: {config.default_provider}\n"
            msg += f"Default Model: {config.default_model}\n"
            msg += f"Threshold: {config.threshold}%\n"
            msg += f"Timeout: {config.timeout}s\n"
            msg += f"Palette: {config.palette}\n"
            msg += f"User Preferences: [dim]{config.user_preferences or 'None set'}[/]\n"
            msg += f"System Prompt: [dim]{config.system_prompt or 'Default'}[/]\n"
            return CommandResult(success=True, message=msg)
        
        if len(args) < 2:
            return CommandResult(success=False, message="Usage: /council config <key> <value>")
            
        key = args[0].lower()
        value = " ".join(args[1:])
        
        from storage.config import save_config
        
        if key == "preferences":
            self.council.config.user_preferences = value
            save_config(self.council.config)
            return CommandResult(success=True, message=f"Updated User Preferences to: [cyan]{value}[/]")
        elif key == "prompt":
            self.council.config.system_prompt = value
            save_config(self.council.config)
            # Update existing agents' prompts
            for agent in self.council.agents:
                agent.system_prompt = value
            return CommandResult(success=True, message=f"Updated Global System Prompt to: [cyan]{value}[/]")
        elif key == "palette":
            valid_palettes = ["default", "cyberpunk", "nord", "dracula"]
            if value.lower() not in valid_palettes:
                return CommandResult(success=False, message=f"Invalid palette. Available: {', '.join(valid_palettes)}")
            
            self.council.config.palette = value.lower()
            save_config(self.council.config)
            # Apply to app immediately
            self.app.set_palette(value.lower())
            return CommandResult(success=True, message=f"Updated Palette to: [cyan]{value}[/]")
        elif key == "model":
            available = [m.name for m in self.council.available_ollama_models]
            if value not in available:
                return CommandResult(success=False, message=f"Model '{value}' not found in Ollama. Available: {', '.join(available[:5])}...")
            
            self.council.config.default_model = value
            save_config(self.council.config)
            return CommandResult(success=True, message=f"Updated default Ollama model to: [cyan]{value}[/]")
        elif key == "threshold":
            try:
                self.council.config.threshold = float(value)
                save_config(self.council.config)
                return CommandResult(success=True, message=f"Updated Threshold to: {value}%")
            except:
                return CommandResult(success=False, message="Threshold must be a number.")
        
        return CommandResult(success=False, message=f"Unknown config key: {key}")

    async def handle_history(self, args: List[str]) -> CommandResult:
        sessions = self.council.session_manager.list_sessions()
        if not sessions:
            return CommandResult(success=True, message="No history found.")
        
        msg = "[bold yellow]Session History:[/bold yellow]\n"
        for s in sessions[:10]: # Last 10
            msg += f"- {s.created_at.strftime('%Y-%m-%d %H:%M')} | {s.query[:30]}... ({s.status})\n"
        return CommandResult(success=True, message=msg)

    async def handle_clear(self, args: List[str]) -> CommandResult:
        self.council.session_manager.clear_sessions()
        return CommandResult(success=True, message="History cleared.")

    async def handle_toggle(self, args: List[str]) -> CommandResult:
        """Toggle the active agents sidebar."""
        self.app.action_toggle_sidebar()
        return CommandResult(success=True, message="Sidebar toggled.")

    async def handle_quit(self, args: List[str]) -> CommandResult:
        self.app.exit()
        return CommandResult(success=True, message="Exiting...")
