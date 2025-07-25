#!/usr/bin/env bash
echo "Running global hooks..."
PATH="/usr/local/bin:$PATH"

if type lint-staged >/dev/null 2>&1; then
  lint-staged --concurrent false -r --config ~/.lintstagedrc || exit 1
else
  echo "lint-staged not installed: npm install lint-staged -g"
  exit 1
fi

exclude_dirs="${EXCLUDE_DIRS:-static/node_modules/pico static/htmx static/hyperscript}"

# Check if there are any changes in the repo
if [[ -n $(git status --porcelain) ]]; then
  echo "Changes detected, running ctags..."
  if ! git ls-files | grep -v -E "^(${exclude_dirs// /|})" |
    ctags -R --exclude=@"$HOME"/.ctagsignore --tag-relative -L - -f"$$.tags"; then
    echo "ctags command failed. Check if ctags is installed and the file patterns are correct."
    exit 1
  fi
  mv "$$.tags" "tags"
  echo "ctags generated successfully."
fi

if [ -f .git/hooks/pre-commit ]; then
  if ! .git/hooks/pre-commit "$@"; then
    echo "local pre-commit hook failed"
    exit 1
  fi
fi

# .lintstagedrc
{
  "*.{yml,yaml}": "yamllint",
  "ansible/*.{yml,yaml}": "ansible-lint --offline",
  "!(node_modules/**/*)*.py": [
    "ruff check"
  ],
  "*.sh": [
    "shellcheck -e SC1090 -e SC2164 -S warning -a -x"
  ]
}
