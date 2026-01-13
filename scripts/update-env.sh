#!/bin/bash
set -euo pipefail

EXAMPLE=".env.example"
TARGET=".env"
PRESERVE_MARKER="# preserved"

normalize_value() {
  local v="$1"

  # Strip surrounding double quotes
  if [[ "$v" == \"*\" ]]; then
    v="${v#\"}"
    v="${v%\"}"
  # Strip surrounding single quotes
  elif [[ "$v" == \'*\' ]]; then
    v="${v#\'}"
    v="${v%\'}"
  fi

  printf '%s' "$v"
}


# If no .env exists, just copy the example BUT continue
# so that the user is warned of missing keys
if [[ ! -f "$TARGET" ]]; then
  cp "$EXAMPLE" "$TARGET"
  echo "Created $TARGET from $EXAMPLE"
fi

# 1. Source existing .env (capture values)
# shellcheck disable=SC1090
set -a
source "$TARGET"
set +a

# Track missing preserved keys
missing_keys=()

# 2. Replace .env with example
rm -f "$TARGET"
cp "$EXAMPLE" "$TARGET"

# 3. Process preserved keys from example
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^[[:space:]]*$ ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ "$line" != *"$PRESERVE_MARKER" ]] && continue
  [[ "$line" != *=* ]] && continue

  key="${line%%=*}"

  # Extract example default value (strip inline comment)
  example_value="${line#*=}"
  example_value="${example_value%%#*}"
  example_value="${example_value%"${example_value##*[![:space:]]}"}"

  user_value="${!key:-}"

  # Normalize both sides
  norm_user="$(normalize_value "$user_value")"
  norm_example="$(normalize_value "$example_value")"

  if [[ "$norm_user" == "$norm_example" ]]; then
    missing_keys+=("$key")
  fi

  # Replace line (strip comments as decided earlier)
  sed -i.bak -E "s|^${key}=.*|${key}=${user_value}|" "$TARGET"
done < "$EXAMPLE"

rm -f "$TARGET.bak"

# 4. Notify user
if (( ${#missing_keys[@]} > 0 )); then
  echo "[WARNING] The following preserved keys were not set in your previous .env:"
  for key in "${missing_keys[@]}"; do
    echo "   - $key"
  done
  echo "   You must update them before proceeding further."
fi

echo "$TARGET updated from $EXAMPLE with preserved values applied >>>"
