[ -n "${STEINS_GREETING_SHOWN:-}" ] && return
STEINS_GREETING_SHOWN=1
case $- in
*i*) [ -n "${BASH_VERSION:-}" ] && printf '\033[38;5;179m  [ S ; O S ]   FUTURE GADGET LABORATORY\033[0m\n  Observe. Question. Create.  |  steins-info\n' ;;
esac
