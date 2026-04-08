import re
from typing import Dict, List
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Button, Label, Static
from textual import events

from utils.models import OllamaModel

def safe_id(model_name: str) -> str:
    """Convert a model name to a safe Textual ID."""
    return re.sub(r'[^a-zA-Z0-9_-]', '-', model_name)

class ModelSelectionModal(ModalScreen[Dict[str, int]]):
    """A modal to select which Ollama models and how many of each to use."""

    def __init__(self, available_models: List[OllamaModel], **kwargs):
        super().__init__(**kwargs)
        self.available_models = available_models
        # State mapping model name to the number of instances requested
        self.selected_models: Dict[str, int] = {model.name: 0 for model in available_models}
        
        # We also need a reverse mapping since we mutate the ID
        self.id_to_model = {safe_id(model.name): model.name for model in available_models}

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-container"):
            yield Label("Select Council Models", classes="modal-title")
            
            with ScrollableContainer(classes="model-list-container"):
                for model in self.available_models:
                    m_id = safe_id(model.name)
                    with Horizontal(classes="model-row"):
                        yield Label(model.name, classes="model-name")
                        yield Button("-", id=f"minus-{m_id}", classes="count-btn")
                        yield Label("0", id=f"count-{m_id}", classes="count-label")
                        yield Button("+", id=f"plus-{m_id}", classes="count-btn")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", id="cancel", variant="error")
                yield Button("Start Council", id="start", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if not button_id:
            return
            
        if button_id == "cancel":
            self.dismiss(None)
        elif button_id == "start":
            # Only return models with count > 0
            result = {name: count for name, count in self.selected_models.items() if count > 0}
            self.dismiss(result)
        elif button_id.startswith("plus-"):
            safe_m_id = button_id[5:]
            model_name = self.id_to_model[safe_m_id]
            self.selected_models[model_name] += 1
            self.query_one(f"#count-{safe_m_id}", Label).update(str(self.selected_models[model_name]))
        elif button_id.startswith("minus-"):
            safe_m_id = button_id[6:]
            model_name = self.id_to_model[safe_m_id]
            if self.selected_models[model_name] > 0:
                self.selected_models[model_name] -= 1
                self.query_one(f"#count-{safe_m_id}", Label).update(str(self.selected_models[model_name]))
