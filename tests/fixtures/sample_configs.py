"""
Sample configuration files for testing.
"""

BASH_CONFIG = """
# Sample .bash_profile configuration
export PATH=$HOME/bin:$PATH

# Basic aliases
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Git aliases
alias gs='git status'
alias gd='git diff'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gco='git checkout'

# Docker aliases
alias dps='docker ps'
alias di='docker images'
alias dc='docker-compose'

# System aliases
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# Functions
function mkcd() {
    mkdir -p "$1" && cd "$1"
}

function extract() {
    if [ -f $1 ] ; then
        case $1 in
            *.tar.bz2)   tar xjf $1     ;;
            *.tar.gz)    tar xzf $1     ;;
            *.bz2)       bunzip2 $1     ;;
            *.rar)       unrar e $1     ;;
            *.gz)        gunzip $1      ;;
            *.tar)       tar xf $1      ;;
            *.tbz2)      tar xjf $1     ;;
            *.tgz)       tar xzf $1     ;;
            *.zip)       unzip $1       ;;
            *.Z)         uncompress $1  ;;
            *.7z)        7z x $1        ;;
            *)     echo "'$1' cannot be extracted via extract()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}
"""

ZSH_CONFIG = """
# Sample .zshrc configuration
export ZSH="$HOME/.oh-my-zsh"

# Theme
ZSH_THEME="robbyrussell"

# Plugins
plugins=(git docker kubectl)

source $ZSH/oh-my-zsh.sh

# User configuration
export PATH=$HOME/bin:/usr/local/bin:$PATH

# Aliases
alias zshconfig="vim ~/.zshrc"
alias ohmyzsh="vim ~/.oh-my-zsh"

# Git aliases (more comprehensive)
alias gs="git status"
alias gst="git status"
alias gd="git diff"
alias gdc="git diff --cached"
alias ga="git add"
alias gaa="git add ."
alias gc="git commit"
alias gcm="git commit -m"
alias gp="git push"
alias gpo="git push origin"
alias gl="git pull"
alias glo="git pull origin"
alias gco="git checkout"
alias gb="git branch"
alias gba="git branch -a"
alias grb="git rebase"
alias gm="git merge"

# Docker aliases
alias dps="docker ps"
alias dpsa="docker ps -a"
alias di="docker images"
alias dc="docker-compose"
alias dcu="docker-compose up"
alias dcd="docker-compose down"
alias dcl="docker-compose logs"

# Kubernetes aliases
alias k="kubectl"
alias kgp="kubectl get pods"
alias kgs="kubectl get services"
alias kgd="kubectl get deployments"
alias kdp="kubectl describe pod"
alias kds="kubectl describe service"

# System aliases
alias ll="ls -la"
alias la="ls -A"
alias l="ls -CF"
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Network aliases
alias ports="lsof -i -P -n | grep LISTEN"
alias myip="curl http://ipecho.net/plain; echo"

# Process aliases
alias psg="ps aux | grep"
alias topcpu="ps aux --sort=-%cpu | head"
alias topmem="ps aux --sort=-%mem | head"
"""


# Configuration with LazySloth already installed
BASH_WITH_LAZYSLOTH = """
# Sample .bash_profile configuration
export PATH=$HOME/bin:$PATH

# Basic aliases
alias ll='ls -la'
alias gs='git status'

# LazySloth integration
lazysloth_preexec() {
    if [ -n "${BASH_COMMAND}" ]; then
        /usr/bin/python3 -m lazysloth.monitors.hook "${BASH_COMMAND}" 2>/dev/null || true
    fi
}
trap 'lazysloth_preexec' DEBUG
# End LazySloth integration
"""

ZSH_WITH_LAZYSLOTH = """
# Sample .zshrc configuration
export ZSH="$HOME/.oh-my-zsh"

alias gs="git status"
alias ll="ls -la"

# LazySloth integration
lazysloth_widget() {
    local cmd_line="$BUFFER"

    if [[ -z "$cmd_line" || "$cmd_line" =~ '^[[:space:]]*$' ]]; then
        zle .accept-line
        return
    fi

    if [[ "$cmd_line" =~ '^[[:space:]]*lazysloth' ]]; then
        zle .accept-line
        return
    fi

    /usr/bin/python3 -m lazysloth.monitors.hook "$cmd_line"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        zle .accept-line
    else
        BUFFER=""
        zle reset-prompt
    fi
}

zle -N lazysloth_widget
bindkey "^M" lazysloth_widget
bindkey "^J" lazysloth_widget
# End LazySloth integration
"""

# Sample aliases data for testing
SAMPLE_ALIASES = {
    "gs": {
        "command": "git status",
        "shell": "zsh",
        "source_file": "/home/user/.zshrc",
        "type": "alias",
    },
    "ll": {
        "command": "ls -la",
        "shell": "bash",
        "source_file": "/home/user/.bash_profile",
        "type": "alias",
    },
    "dps": {
        "command": "docker ps",
        "shell": "zsh",
        "source_file": "/home/user/.zshrc",
        "type": "alias",
    },
    "gco": {
        "command": "git checkout",
        "shell": "bash",
        "source_file": "/home/user/.bash_profile",
        "type": "alias",
    },
}

# Sample statistics data for testing
SAMPLE_STATS = {
    "gs": {
        "count": 5,
        "first_seen": "2024-01-01T10:00:00",
        "last_seen": "2024-01-01T15:00:00",
        "alias_command": "git status",
    },
    "ll": {
        "count": 2,
        "first_seen": "2024-01-01T11:00:00",
        "last_seen": "2024-01-01T14:00:00",
        "alias_command": "ls -la",
    },
    "dps": {
        "count": 1,
        "first_seen": "2024-01-01T12:00:00",
        "last_seen": "2024-01-01T12:00:00",
        "alias_command": "docker ps",
    },
}
