from storage.config import load_config, save_config
import os

def test_save():
    config = load_config()
    print(f"Loaded palette: {config.palette}")
    
    # Change to something different
    new_palette = "cyberpunk" if config.palette != "cyberpunk" else "nord"
    print(f"Setting palette to: {new_palette}")
    config.palette = new_palette
    save_config(config)
    
    # Reload and check
    config2 = load_config()
    print(f"Reloaded palette: {config2.palette}")
    
    if config2.palette == new_palette:
        print("SUCCESS: Palette saved and loaded correctly.")
    else:
        print("FAILURE: Palette not saved.")

if __name__ == "__main__":
    test_save()
