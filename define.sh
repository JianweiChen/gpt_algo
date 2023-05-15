
declare -g  __out_key
declare -g  __out_val
declare -ag __out_array

function exit_with() {
    declare exit_code=5
    declare func_stack="${FUNCNAME[@]:1}"
    declare tip="${1}"
    declare message="exit ${exit_code}: stack~~($func_stack) tip~~ ${tip}"
    echo "$message">&2
    exit "$exit_code"
}
function parse_kv() {
    declare input_string="$1"
    declare key="${input_string%%=*}"
    declare val="${input_string#*=}"
    declare key_regex="^[a-zA-Z0-9_]+$"
    [[ -z "$key" ]] && { exit_with "key empty ${input_string}"; }
    [[ $key =~ $key_regex ]] || { exit_with "key format error: $key"; }
    [[ "$val" = "$input_string" ]] && { val=yep; }
    [[ "$val" = "no" ]] && { val=""; }
    __out_key="${key}"
    __out_val="${val}"
    __out_array=("${key}" "${val}")
}

declare -r heredoc_option=$(cat <<'script_code'
for __option_name in ${__option_names[@]}; do
    declare "__option_${__option_name}="
done
declare option_regex="--[^-]+"
while true; do
    part="$1"
    [[ $part =~ $option_regex ]] || { break; }
    part="${part#--}"
    parse_kv "$part"
    __out_key="__option_${__out_key}"
    declare "$__out_key=$__out_val"
    shift
done
script_code
)

function show_array() {
    declare array_name="$1"
    echo -e "ARRAY $array_name:"
    eval "for el in \"\${$array_name[@]}\"; do echo - \$el; done"
}

function define() {
    eval "${heredoc_option:?}"
    parse_kv "$1"
    if [[ -z "$__option_empty" ]]; then
        [[ -n "$__out_val" ]] || { exit_with "val empty, key=$__out_key"; }
    fi
    # because $_ is special
    if [[ $__out_key != _  ]]; then
        declare -g "$1"
    fi
}

function define-port() {
    eval "${heredoc_option:?}"
    parse_kv "$1"
    [[ "$__out_val" -lt 10 ]] && { exit_with "value --lt 10: but got $__out_val"; }
    define "$__out_key=$__out_val"
}

function define-pid() {
    eval "${heredoc_option:?}"
    parse_kv "$1"
    if [[ -n "$__option_from_port" ]]; then
        declare -i __option_from_port=$__option_from_port
        declare pids="$(lsof -i :$__option_from_port -sTCP:LISTEN -n -P -t)"
        declare -a __array=($pids)
        declare __out_val="${__array[0]:-<this is not a pid>}"
    elif [[ -n "$__option_cmd" ]]; then
        declare cmd="$__option_cmd; echo done | format --color=34 --stderr"
        if [[ -n "$__option_log" ]]; then
            if [[ -n "$__option_with_stamp" ]]; then
                eval "($cmd)" > >(format --with_stamp >> $__option_log) 2> >(format --with_stamp --stderr >> $__option_log) &
            else
                eval "($cmd)" 1>>$__option_log 2>>$__option_log &
            fi
        else
            if [[ -n "$__option_with_stamp" ]]; then
                eval "($cmd)" | format --with_stamp
            else
                eval "($cmd)" &
            fi
        fi
        declare pid=$!
        __out_val=${pid:-"<this is not pid>"}
    else
        [[ "$__out_val" -lt 1000 ]] && { exit_with "value --lt 1000: but got $__out_val"; }
    fi
    define "$__out_key=$__out_val"
}

function define-dir() {
    eval "${heredoc_option:?}"
    parse_kv "$1"
    if [[ -n "$__option_create" ]] && [[ -n "$__out_val" ]]; then
        mkdir -p "$__out_val"
    fi
    [[ -d "$__out_val" ]] || { exit_with "directory not exist: $__out_key=$__out_val"; }
    define "$__out_key=$__out_val"
}
function define-file() {
    eval "${heredoc_option:?}"
    parse_kv "$1"
    if [[ -n "$__option_create" ]] && [[ -n "$__out_val" ]]; then
        declare dirpath=$(dirname "$__out_val")
        [[ -n "$dirpath" ]] && { mkdir -p "$dirpath"; touch "$__out_val"; }
    fi
    [[ -f "$__out_val" ]] || { exit_with "file not exist: $__out_key=$__out_val"; }
    define "$__out_key=$__out_val"
}

function format() {
    __option_names=(wave stderr color with_stamp)
    eval "${heredoc_option:?}"
    [[ -n "$__option_with_stamp" ]] && { 
        declare log_id="$RANDOM"
        declare i=0
        declare start_timestamp=`TZ='Asia/Shanghai' date +%H:%M:%S`
        declare mark="I"
        [[ -n "$__option_stderr" ]] && { mark=$(echo -e "\e[91mW\e[0m"); }
    }
    while read message; do
        [[ -n "$__option_with_stamp" ]] && {
            printf "[%s %s %s %s %s] %s\n" "$mark" "$log_id"  "$start_timestamp" "$SECONDS" "$i" "$message"
            # printf "[%s %05s %05s %5s %5s] %s\n" "$mark" "$log_id"  "$start_timestamp" "$SECONDS" "$i" "$message"

            ((i+=1))
            continue
        }
        [[ -n "$__option_wave" ]] && { message="~~~~~~~~~~~~~~~~ $message ~~~~~~~~~~~~~~~~"; }
        [[ -n "$__option_color" ]] && { message="\e[${__option_color/yep/31}m${message}\e[0;0m"; }
        if [[ -n "$__option_stderr" ]]; then
            echo -e "$message" >&2
        else
            echo -e "$message"
        fi
    done
}
