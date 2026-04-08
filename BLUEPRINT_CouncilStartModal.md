# Architectural Blueprint: Council Start Modal

## 1. Executive Summary
Implementing an interactive Textual `ModalScreen` that appears when the user types `/council start`. This modal will display all available Ollama models, allowing users to intuitively select and deselect agents by interacting with a counter for each model. This fully supports instantiating multiple agents of the exact same model type.

## 2. Dependency Matrix
- **Runtime/Framework:** Python 3.11+, Textual (currently installed)
- **Core Libraries:**
  - `textual`: For creating the `ModalScreen`, layout containers (`Horizontal`, `Vertical`), and interactive widgets (`Button`, `Label`).

## 3. Data Models & Schemas
- No new persistent data schemas are required. 
- The modal will manage an in-memory state dictionary `Dict[str, int]` mapping model names to the number of requested agent instances.

## 4. System Architecture & Flow
1. User types `/council start` and submits the command.
2. `CommandHandler.handle_start` intercepts the command and triggers `self.app.push_screen(ModelSelectionModal)`.
3. The `ModelSelectionModal` receives the list of `available_ollama_models`.
4. The user clicks `+` or `-` buttons next to each model to increment/decrement the count (selecting/deselecting).
5. The user clicks the "Start Council" button.
6. The modal calls `self.dismiss(selected_models_dict)`.
7. A callback function in the main `App` receives the dictionary, clears the existing council agents, and loops through the dictionary to repeatedly call `council.add_agent("ollama", model_name)` for each requested instance.
8. The callback logs the initialization message and updates the active agents sidebar.

## 5. Directory Structure
```
cli/
├── commands.py      (modified to push modal)
├── interface.py     (modified to handle modal callback)
├── start_modal.py   (NEW file for the ModalScreen)
└── styles.tcss      (modified for modal layout styling)
```

## 6. Step-by-Step Implementation Guide

### Phase 1: Modal UI Construction (`cli/start_modal.py`)
1. Create `cli/start_modal.py`.
2. Define a `ModelSelectionModal(ModalScreen[dict])` class.
3. In `compose()`, structure the UI: 
   - A central `Vertical` container with a title.
   - A `ScrollableContainer` listing available models.
   - For each model, yield a `Horizontal` container holding: `Label(model_name)`, `Button("-", id=f"minus|{model_name}")`, `Label("0", id=f"count|{model_name}")`, `Button("+", id=f"plus|{model_name}")`.
   - A `Horizontal` container at the bottom with `Button("Cancel", id="cancel")` and `Button("Start Council", id="start", variant="success")`.
4. Implement `on_button_pressed` to capture clicks:
   - Parse button ID. If `plus|{model}`, increment the specific count label and update the internal state dict.
   - If `minus|{model}`, decrement (minimum 0) and update state.
   - If `cancel`, call `self.dismiss(None)`.
   - If `start`, call `self.dismiss(self.selected_models)`.

### Phase 2: Core Integration (`cli/commands.py` & `cli/interface.py`)
1. In `cli/commands.py -> handle_start`, verify `self.council.available_ollama_models` is not empty.
2. Instead of directly adding agents, invoke a new method on `self.app`, e.g., `self.app.show_start_modal(self.council.available_ollama_models)`.
3. In `cli/interface.py`, implement `show_start_modal`. It will push the `ModelSelectionModal` and define a callback function `_on_modal_dismiss(result: dict)`.
4. In `_on_modal_dismiss`, if `result` is not None:
   - Clear existing agents: `self.council.agents = []`.
   - Loop over `result.items()`. If count > 0, run `self.council.add_agent("ollama", model_name)` *count* times.
   - Run `self.update_agent_list()`.
   - Output success message via `self.log_message`.

### Phase 3: Styling (`cli/styles.tcss`)
1. Add CSS rules in `cli/styles.tcss` for the modal.
2. E.g., style `ModelSelectionModal` with `align: center middle; background: $background 50%;`.
3. Create a `.modal-container` class to set fixed dimensions and borders.
4. Style the `Horizontal` model rows to use `align: right middle;` for the buttons and `width: 100%;` to spread out the model name and the counter.
