#!/bin/sh
launcher_dir=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd) || exit 1
game_dir="$launcher_dir/blade-shooter"
launcher_log="$launcher_dir/blade_shooter_launch.log"
if (umask 077; : > "$launcher_log") 2>/dev/null; then
    exec > "$launcher_log" 2>&1
fi
printf '%s\n' 'Blade Close Quarters GKD launcher'
date
printf 'Game directory: %s\n' "$game_dir"
if [ ! -f "$game_dir/main.py" ]; then
    printf '%s\n' 'Cannot find blade-shooter/main.py beside this launcher.' >&2
    exit 1
fi
cd "$game_dir" || exit 1
game_python=${BLADE_SHOOTER_PYTHON:-/storage/pyxel_Python/bin/python3}
if [ ! -x "$game_python" ]; then
    printf 'Python executable not found: %s\n' "$game_python" >&2
    exit 1
fi
printf 'Python: %s\n' "$game_python"
exec "$game_python" -u main.py --gkd "$@"
