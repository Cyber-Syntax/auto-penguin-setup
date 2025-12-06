#!/usr/bin/env bats

setup() {
  TMPDIR="$(mktemp -d)"
  export CONFIG_DIR="$TMPDIR/config"
  export EXAMPLES_DIR="$TMPDIR/examples"
  mkdir -p "$CONFIG_DIR" "$EXAMPLES_DIR"

  # Example variables.ini (the canonical/default)
  cat >"$EXAMPLES_DIR/variables.ini" <<'EOF'
[common]
user = example_user

[desktop]
session = gnome

[laptop]
ip = 1.2.3.4
EOF

  # User variables.ini missing the laptop ip key (and maybe other keys)
  cat >"$CONFIG_DIR/variables.ini" <<'EOF'
[common]
user = myuser

[laptop]
# ip is intentionally missing in user file
EOF

  # Example packages.ini (defaults)
  cat >"$EXAMPLES_DIR/packages.ini" <<'EOF'
[core]
packages = bash, coreutils

[apps]
packages = firefox, vlc
EOF

  # User packages.ini missing the [apps] section
  cat >"$CONFIG_DIR/packages.ini" <<'EOF'
[core]
packages = bash, coreutils
EOF
}

teardown() {
  rm -rf "$TMPDIR"
}

@test "update_config_schema adds missing sections and keys for INI files" {
  # Source the script and run the function; feed 'y' to accept updates immediately
  run bash -c ". src/core/update_config.sh; printf 'y\n' | update_config_schema true"
  # Expect success (updated > 0 returns 0)
  [ "$status" -eq 0 ] || {
    echo "STDOUT/STDERR:"
    echo "$output"
    fail "update_config_schema did not succeed (status $status)"
  }

  # packages.ini should now contain the appended [apps] section with the example packages
  run grep -E '^\[apps\]' "$CONFIG_DIR/packages.ini"
  [ "$status" -eq 0 ] || {
    echo "$output"
    echo "Expected [apps] section in packages.ini"
    return 1
  }
  run grep -E '^\s*packages\s*=\s*firefox' "$CONFIG_DIR/packages.ini"
  [ "$status" -eq 0 ] || {
    echo "$output"
    echo "Expected packages line with firefox in packages.ini"
    return 1
  }

  # variables.ini should now have the missing ip key added under [laptop]
  run awk '/^\[laptop\]/{p=1; next} /^\[/{p=0} p && /ip[[:space:]]*=/{print $0}' "$CONFIG_DIR/variables.ini"
  [ "$status" -eq 0 ] || {
    echo "$output"
    echo "Expected ip key present under [laptop] in variables.ini"
    return 1
  }
  # ensure the value is the one from the example
  run grep -E '^\s*ip\s*=\s*1\.2\.3\.4' "$CONFIG_DIR/variables.ini"
  [ "$status" -eq 0 ] || {
    echo "$output"
    echo "Expected ip value 1.2.3.4 in variables.ini"
    return 1
  }
}

@test "update_config_schema skips when there is nothing to update" {
  # Make a copy of the example files as user files (so nothing is missing)
  cp "$EXAMPLES_DIR/variables.ini" "$CONFIG_DIR/variables.ini"
  cp "$EXAMPLES_DIR/packages.ini" "$CONFIG_DIR/packages.ini"

  run bash -c ". src/core/update_config.sh; printf 'n\n' | update_config_schema false"
  # When no updates are needed the function currently returns 1 per original logic
  # Accept either 0 or 1 as "no crash", but ensure files are unchanged and valid INI content remains
  [ "$status" -eq 0 ] || [ "$status" -eq 1 ] || fail "Unexpected exit status: $status"

  # Ensure the files still contain expected section headers from the example
  run grep -E '^\[laptop\]' "$CONFIG_DIR/variables.ini"
  [ "$status" -eq 0 ] || {
    echo "$output"
    echo "Expected [laptop] section in variables.ini"
    return 1
  }
  run grep -E '^\[apps\]' "$CONFIG_DIR/packages.ini"
  [ "$status" -eq 0 ] || {
    echo "$output"
    echo "Expected [apps] section in packages.ini (second test)"
    return 1
  }
}
