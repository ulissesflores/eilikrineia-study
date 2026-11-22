# One real trial from the frozen audit: the agent says the work is done, the hidden check fails.
# Recorded with charmbracelet/vhs from the repository root: vhs assets/demo/case-light.tape
Output assets/demo/case-light.gif
Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 560
Set Padding 24
Set Theme "Builtin Light"
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
