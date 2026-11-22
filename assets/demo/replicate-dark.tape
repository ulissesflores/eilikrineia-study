# Replication without any model call: analyses rerun, published numbers checked, seal verified.
# Recorded with charmbracelet/vhs from the repository root: vhs assets/demo/replicate-dark.tape
Output assets/demo/replicate-dark.gif
Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 520
Set Padding 24
Set Theme { "name": "repo-dark", "background": "#0d1117", "foreground": "#e6edf3", "cursor": "#e6edf3", "selection": "#30363d", "black": "#484f58", "red": "#ff7b72", "green": "#3fb950", "yellow": "#d29922", "blue": "#58a6ff", "magenta": "#bc8cff", "cyan": "#39c5cf", "white": "#b1bac4", "brightBlack": "#6e7681", "brightRed": "#ffa198", "brightGreen": "#56d364", "brightYellow": "#e3b341", "brightBlue": "#79c0ff", "brightMagenta": "#d2a8ff", "brightCyan": "#56d4dd", "brightWhite": "#f0f6fc" }
Set TypingSpeed 35ms
Env PS1 "$ "
Env PYTHONDONTWRITEBYTECODE "1"
Hide
Type "source .venv/bin/activate && clear" Enter
Show
Type "# Rerun the analyses, check the published numbers, verify the seal (offline)" Enter
Sleep 600ms
Type "python run_all.py" Enter
Sleep 7s
Type "# The seal also verifies by itself, standard library only:" Enter
Type "python make_provenance.py --verify" Enter
Sleep 3s
