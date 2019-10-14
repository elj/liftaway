#!/usr/bin/env bash

function get_script_dir () {
     SOURCE="${BASH_SOURCE[0]}"
     while [ -h "$SOURCE" ]; do
          DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
          SOURCE="$( readlink "$SOURCE" )"
          [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
     done
     $( cd -P "$( dirname "$SOURCE" )" )
     pwd
}

function keep_alive() {
    local PYTHON="${HOME}/.pyenv/versions/liftaway/bin/python3"
    while true; do
        command "${PYTHON}" ${HOME}/src/github.com/elj/liftaway/liftaway/lift_main.py
        sleep 3 || break;
    done
}

function tmux_session() {
    local DIRECTORY="$1"
    shift
    local SESSION="${1:-$(basename "${DIRECTORY}")}"
    shift
    local COMMAND="${1}"
    [[ -d "${DIRECTORY}" ]] || return 248
    command tmux has-session -t "${SESSION}" &>/dev/null && return 2
    if [[ -n "${COMMAND}" ]]; then
        command tmux new-session -c "${DIRECTORY}" -s "${SESSION}" -d "${COMMAND}"
    else
        command tmux new-session -c "${DIRECTORY}" -s "${SESSION}" -d
    fi
}

function start() {
    local TMS="local"
    command tmux start-server &>/dev/null
    tmux_session ${HOME} "${TMS}" ${HOME}/src/github.com/elj/liftaway/scripts/keep_alive
    command tmux attach -t "${TMS}"
}

[ "`type -t "${0##*/}"`" = "function" ] && \
{ "${0##*/}" ${@} ; exit $? ; } || \
{ echo "Unknown function: ${0##*/}" > /dev/stderr ; exit 254 ; };
