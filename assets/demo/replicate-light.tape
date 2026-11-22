# Replication without any model call: analyses rerun, published numbers checked, seal verified.
# Recorded with charmbracelet/vhs from the repository root: vhs assets/demo/replicate-light.tape
Output assets/demo/replicate-light.gif
Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 520
Set Padding 24
Set Theme "Builtin Light"
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
