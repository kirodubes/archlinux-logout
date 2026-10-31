#!/bin/bash
set -euo pipefail
#####################################################################
# Author    : Erik Dubois
# Website   : https://kiroproject.be
#####################################################################
#
#   DO NOT JUST RUN THIS. EXAMINE AND JUDGE. RUN AT YOUR OWN RISK.
#
#   Purpose:
#   - Extract every _() / ngettext() string from the app into
#     po/ohmychadwm-tweak-tool.pot.
#   - Merge that template into each po/<lang>.po: a changed English
#     string turns fuzzy, a removed one obsolete.
#   - Compile each <lang>.po into
#     usr/share/locale/<lang>/LC_MESSAGES/ohmychadwm-tweak-tool.mo,
#     which the package ships as is.
#   - Write the menu entry from po/ohmychadwm-tweak-tool.desktop.in
#     with every language's Name/Comment/Keywords added. Edit the .in
#     file, never usr/share/applications/ (it is overwritten).
#
#   Why: run it after any change to the app's text, before the flow
#   script builds the package, so the shipped .mo files match the code.
#
#####################################################################

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

#####################################################################
# Colors
#####################################################################
if command -v tput >/dev/null 2>&1 && [[ -t 1 ]]; then
    RED="$(tput setaf 1)"
    GREEN="$(tput setaf 2)"
    YELLOW="$(tput setaf 3)"
    BLUE="$(tput setaf 4)"
    CYAN="$(tput setaf 6)"
    RESET="$(tput sgr0)"
else
    RED="" GREEN="" YELLOW="" BLUE="" CYAN="" RESET=""
fi

#####################################################################
# Logging
#####################################################################
log_section() {
    echo
    echo "${GREEN}############################################################################${RESET}"
    echo "$1"
    echo "${GREEN}############################################################################${RESET}"
    echo
}

log_info() {
    echo
    echo "${BLUE}############################################################################${RESET}"
    echo "$1"
    echo "${BLUE}############################################################################${RESET}"
    echo
}

log_warn() {
    echo
    echo "${YELLOW}############################################################################${RESET}"
    echo "$1"
    echo "${YELLOW}############################################################################${RESET}"
    echo
}

log_error() {
    echo
    echo "${RED}############################################################################${RESET}"
    echo "$1"
    echo "${RED}############################################################################${RESET}"
    echo
}

log_success() {
    echo
    echo "${GREEN}############################################################################${RESET}"
    echo "$1"
    echo "${GREEN}############################################################################${RESET}"
    echo
}

#####################################################################
# Error handling
#####################################################################
on_error() {
    echo "${RED}ERROR on line $1: $2${RESET}"
    sleep 10
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

#####################################################################
# Functions
#####################################################################
DOMAIN="archlinux-betterlockscreen"
REPO="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
POT="$SCRIPT_DIR/$DOMAIN.pot"
DESKTOP_IN="$SCRIPT_DIR/$DOMAIN.desktop.in"
DESKTOP="$REPO/usr/share/applications/$DOMAIN.desktop"

extract() {
    log_section "Extracting the strings into $(basename "$POT")"
    (cd "$REPO" && xgettext --language=Python --from-code=UTF-8 --keyword=_ --keyword=N_ --keyword=ngettext:1,2 \
        --add-comments=TRANSLATORS --package-name="$DOMAIN" --sort-by-file \
        -o "$POT" usr/share/"$DOMAIN"/*.py)
    # relative paths only: the source comments in the .pot must not carry a home folder
    (cd "$REPO" && xgettext --language=Desktop --join-existing -o "$POT" "po/$DOMAIN/$(basename "$DESKTOP_IN")")
    log_info "${CYAN}$(grep -c '^msgid ' "$POT")${RESET} entries (the first is the header)"
}

merge_and_compile() {
    local po lang mo
    for po in "$SCRIPT_DIR"/*.po; do
        [[ -e "$po" ]] || continue
        lang="$(basename "$po" .po)"
        log_section "$lang"
        msgmerge --quiet --update --backup=none "$po" "$POT"
        mo="$REPO/usr/share/locale/$lang/LC_MESSAGES/$DOMAIN.mo"
        mkdir -p "$(dirname "$mo")"
        # --check also verifies that every {placeholder} of the English survives in the translation
        msgfmt --check --statistics -o "$mo" "$po"
    done
}

write_desktop() {
    log_section "Menu entry"
    # msgfmt --desktop reads the languages from po/LINGUAS
    find "$SCRIPT_DIR" -maxdepth 1 -name '*.po' -printf '%f\n' | sed 's/\.po$//' | sort > "$SCRIPT_DIR/LINGUAS"
    msgfmt --desktop --template="$DESKTOP_IN" -d "$SCRIPT_DIR" -o "$DESKTOP"
    log_info "$(basename "$DESKTOP") written"
}

#####################################################################
# Main
#####################################################################
main() {
    extract
    merge_and_compile
    write_desktop
    log_success "$(basename "$0") done"
}

main "$@"
