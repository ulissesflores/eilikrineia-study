# One real trial from the frozen audit: the agent says the work is done, the hidden check fails.
# Recorded with charmbracelet/vhs from the repository root: vhs assets/demo/case-dark.tape
Output assets/demo/case-dark.gif
Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 560
Set Padding 24
Set Theme { "name": "repo-dark", "background": "#0d1117", "foreground": "#e6edf3", "cursor": "#e6edf3", "selection": "#30363d", "black": "#484f58", "red": "#ff7b72", "green": "#3fb950", "yellow": "#d29922", "blue": "#58a6ff", "magenta": "#bc8cff", "cyan": "#39c5cf", "white": "#b1bac4", "brightBlack": "#6e7681", "brightRed": "#ffa198", "brightGreen": "#56d364", "brightYellow": "#e3b341", "brightBlue": "#79c0ff", "brightMagenta": "#d2a8ff", "brightCyan": "#56d4dd", "brightWhite": "#f0f6fc" }
Set TypingSpeed 35ms
Env PS1 "$ "
Env PYTHONDONTWRITEBYTECODE "1"
Hide
Type "clear" Enter
Show
Type "# What a false completion looks like: one audited trial of study 3" Enter
Sleep 600ms
Type "python3 scripts/show_case.py" Enter
Sleep 7s
