# Steins;OS interactive Bash prompt and greeting.
#
# Sourced by /etc/profile.d/steins.sh for interactive Bash login shells (the
# terminal opens login shells). It never edits ~/.bashrc. On the first prompt it
# replaces only Debian's stock prompt; a PS1 you have customised is left alone.
#
#   STEINS_PROMPT=off     keep your own/Debian's prompt
#   STEINS_PROMPT=on      use this prompt even if ~/.bashrc customised PS1
#   STEINS_GREETING=off   no greeting line (an empty ~/.hushlogin works too)
#
# Colours are ANSI indices, so the terminal's worldline palette recolours them:
# 3 = worldline accent (user/host, chevron), 6 = cyan (path), 8 = worldline muted.

[ -n "${BASH_VERSION:-}" ] || return 0
case $- in *i*) ;; *) return 0 ;; esac
[ -z "${__steins_prompt_loaded:-}" ] || return 0
__steins_prompt_loaded=1

__steins_greeting() {
    [ "${STEINS_GREETING:-}" = off ] && return 0
    [ -e "$HOME/.hushlogin" ] && return 0
    [ -t 1 ] || return 0
    local divergence='' file
    for file in "$HOME/.local/state/steins/divergence" /etc/steins/default-divergence; do
        if [ -r "$file" ]; then
            IFS= read -r divergence < "$file" || true
            [[ $divergence =~ ^[0-9]+\.[0-9]{6}$ ]] && break
            divergence=''
        fi
    done
    if [ "${TERM:-dumb}" = dumb ] || [ -n "${NO_COLOR:-}" ]; then
        printf 'Steins;OS%s  -  steins-info for system details\n\n' "${divergence:+  -  divergence $divergence}"
    else
        printf '\033[33mSteins;OS\033[0m\033[90m%s  ·  \033[0m\033[36msteins-info\033[0m\033[90m for system details\033[0m\n\n' \
            "${divergence:+  ·  divergence $divergence}"
    fi
}

# Sets __steins_ps_git from .git/HEAD without running git or forking, so it is
# cheap enough for every prompt. Worktrees/submodules (".git" files) are followed.
__steins_git_branch() {
    __steins_ps_git=''
    local dir=$PWD head='' gitdir=''
    while :; do
        if [ -d "$dir/.git" ]; then
            gitdir=$dir/.git
            break
        elif [ -f "$dir/.git" ]; then
            IFS= read -r gitdir < "$dir/.git" 2>/dev/null || return 0
            gitdir=${gitdir#gitdir: }
            [[ $gitdir == /* ]] || gitdir=$dir/$gitdir
            break
        fi
        [ -z "$dir" ] && return 0
        dir=${dir%/*}
    done
    [ -r "$gitdir/HEAD" ] || return 0
    IFS= read -r head < "$gitdir/HEAD" 2>/dev/null || [ -n "$head" ] || return 0
    case $head in
        'ref: refs/heads/'*) __steins_ps_git=${head#ref: refs/heads/} ;;
        ????????*) __steins_ps_git=${head:0:7} ;;
    esac
    return 0
}

__steins_prompt_is_stock() {
    # Debian's /etc/skel/.bashrc and /etc/bash.bashrc prompts, with and without the xterm title prefix.
    local p=$1 title colour plain
    colour='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
    plain='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
    title="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]"
    case $p in
        "$colour" | "$plain" | "$title$colour" | "$title$plain" | '\s-\v\$ ') return 0 ;;
    esac
    return 1
}

__steins_prompt_build() {
    local glyph='❯' title=''
    case "${TERM:-dumb}:${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
        linux:* | dumb:* | *:C | *:POSIX | *:) glyph='>' ;;
    esac
    [ "${EUID:-1}" = 0 ] && glyph='#'
    case ${TERM:-} in xterm* | vte* | rxvt* | tmux* | screen* | alacritty | foot* | kitty*)
        title='\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]' ;;
    esac
    local who='\[\e[33m\]\u@\h\[\e[0m\]'
    [ "${EUID:-1}" = 0 ] && who='\[\e[31m\]\u@\h\[\e[0m\]'
    PS1=$title'${debian_chroot:+\[\e[90m\]($debian_chroot)\[\e[0m\] }'$who
    PS1+=' \[\e[36m\]\w\[\e[0m\]'
    PS1+='${__steins_ps_git:+ \[\e[90m\]on \[\e[0m\]\[\e[33m\]$__steins_ps_git\[\e[0m\]}'
    PS1+='${__steins_ps_took:+ \[\e[90m\]took $__steins_ps_took\[\e[0m\]}'
    PS1+='${__steins_ps_status:+ \[\e[31m\]exit $__steins_ps_status\[\e[0m\]}'
    PS1+=' \[\e[${__steins_ps_chevron:-33}m\]'$glyph'\[\e[0m\] '
    PS2='\[\e[90m\]·\[\e[0m\] '
    [ "$glyph" = '>' ] && PS2='> '
    PROMPT_DIRTRIM=${PROMPT_DIRTRIM:-3}
}

__steins_prompt_hook() {
    local status=$?
    if [ -z "${__steins_prompt_state:-}" ]; then
        __steins_prompt_state=off
        case ${STEINS_PROMPT:-} in
            off) ;;
            on) __steins_prompt_state=on ;;
            *) __steins_prompt_is_stock "$PS1" && __steins_prompt_state=on ;;
        esac
        __steins_greeting
        [ "$__steins_prompt_state" = on ] || return "$status"
        __steins_prompt_build
        # PS0 is expanded when a command line is accepted: remember its start time.
        # Prepended: VTE's PS0 ends in an ESC-backslash terminator that would
        # escape anything appended after it. This expansion prints nothing.
        PS0='${__steins_nil[__steins_t0=SECONDS,0]-}'${PS0-}
    fi
    [ "$__steins_prompt_state" = on ] || return "$status"
    __steins_ps_took='' __steins_ps_status='' __steins_ps_chevron=33
    if [ -n "${__steins_t0:-}" ]; then
        local elapsed=$((SECONDS - __steins_t0))
        if ((elapsed >= 3600)); then __steins_ps_took="$((elapsed / 3600))h $((elapsed % 3600 / 60))m"
        elif ((elapsed >= 60)); then __steins_ps_took="$((elapsed / 60))m $((elapsed % 60))s"
        elif ((elapsed >= 5)); then __steins_ps_took="${elapsed}s"
        fi
        if [ "$status" != 0 ]; then
            __steins_ps_status=$status
            __steins_ps_chevron=31
        fi
        unset __steins_t0
    fi
    __steins_git_branch
    return "$status"
}

# Run first so the hook sees the command's exit status. Bash 5.1+ accepts an
# array here; Debian's VTE integration (/etc/profile.d/vte-2.91.sh) appends to
# an array but would overwrite a plain string.
if ((BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 1))); then
    if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == 'declare -a'* ]]; then
        PROMPT_COMMAND=(__steins_prompt_hook "${PROMPT_COMMAND[@]}")
    else
        PROMPT_COMMAND=(__steins_prompt_hook ${PROMPT_COMMAND:+"$PROMPT_COMMAND"})
    fi
else
    PROMPT_COMMAND="__steins_prompt_hook${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
fi
