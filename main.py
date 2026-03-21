import typer
from cli.interface import CouncilApp

def main():
    """Start the Council AI Research Terminal."""
    council_app = CouncilApp()
    council_app.run()

if __name__ == "__main__":
    typer.run(main)
