import sys
import os

# Add current directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import MusicPlayerGUI


def main():
    """Main entry point for Harmonix Music Player."""
    print("Launching Harmonix Music Player...")
    app = MusicPlayerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
