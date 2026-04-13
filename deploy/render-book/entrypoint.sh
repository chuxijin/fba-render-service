#!/bin/sh
set -eu

CUSTOM_FONT_SRC="${RENDER_SERVICE_FONTS_ROOT:-/app/render_service/fonts}"
CUSTOM_FONT_DST="/usr/local/share/fonts/render-book-custom"

mkdir -p "${CUSTOM_FONT_DST}"

if [ -d "${CUSTOM_FONT_SRC}" ]; then
  find "${CUSTOM_FONT_SRC}" -maxdepth 1 -type f \( -iname '*.otf' -o -iname '*.ttf' -o -iname '*.ttc' \) -exec cp -f {} "${CUSTOM_FONT_DST}"/ \;
fi

fc-cache -fv >/dev/null 2>&1 || true

exec "$@"
