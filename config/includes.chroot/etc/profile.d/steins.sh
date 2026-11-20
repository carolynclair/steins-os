# Steins;OS interactive shell integration (login shells; the terminal opens them).
# Bash gets the Steins;OS prompt and a one-line greeting from
# /usr/share/steins/shell/prompt.bash. Nothing runs for scripts or other shells.
# Opt out per user with STEINS_PROMPT=off / STEINS_GREETING=off, or ~/.hushlogin.
case $- in
*i*)
    if [ -n "${BASH_VERSION:-}" ] && [ -r /usr/share/steins/shell/prompt.bash ]; then
        . /usr/share/steins/shell/prompt.bash
    fi
    ;;
esac
