#!/bin/bash
# Reproducible host mock test runner for the proxy-consumer driver suites.
#
# Usage: run_tests.sh /path/to/kernel/worktree [workdir]
#   The worktree must have drivers/regulator/proxy-consumer.c and
#   include/linux/regulator/proxy-consumer.h (e.g. the pinned ACK
#   8ad08f75 with the Stage A series applied).
#   workdir defaults to the directory containing this script.
#
# The harness compiles the REAL driver source into two standalone host
# test programs through the mock tree in mock/ and runs them.  Expected
# output: legacy suite "checks=38 failures=0", ROUND32 suite
# "checks=73 failures=0".
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
A="${1:?usage: run_tests.sh /path/to/kernel/worktree [workdir]}"
T="${2:-$SCRIPT_DIR}"
SRC="$A/drivers/regulator/proxy-consumer.c"
HDR="$A/include/linux/regulator/proxy-consumer.h"
[ -f "$SRC" ] || { echo "driver source not found: $SRC" >&2; exit 2; }
[ -f "$HDR" ] || { echo "driver header not found: $HDR" >&2; exit 2; }

mkdir -p "$T/mock/linux/regulator"
for h in device err kernel limits list mutex of slab; do
  printf '#include <mock_core.h>\n' > "$T/mock/linux/$h.h"
done
printf '#include <mock_core.h>\n' > "$T/mock/linux/regulator/consumer.h"
printf '#include <mock_core.h>\n' > "$T/mock/linux/regulator/driver.h"
cp -f "$HDR" "$T/mock/linux/regulator/proxy-consumer.h"
# errno.h is provided as a static shim in the repo; do not regenerate it.

FAIL=0
for suite in test_proxy_consumer_r31 test_proxy_consumer_round32; do
  echo "--- $suite ---"
  echo "source sha256: $(sha256sum "$SRC" | cut -d' ' -f1)"
  gcc -std=gnu11 -DCONFIG_REGULATOR_PROXY_CONSUMER=1 -Wall -Wextra \
      -Wno-unused-parameter -O1 \
      -I "$T/mock" -I "$A/include" -I "$A" \
      -o "/tmp/$suite" "$T/$suite.c" 2>&1
  RC=$?
  echo "COMPILE_RC=$RC"
  [ $RC -ne 0 ] && { FAIL=1; continue; }
  "/tmp/$suite"
  RC=$?
  echo "TEST_RC=$RC"
  [ $RC -ne 0 ] && FAIL=1
done
[ $FAIL -eq 0 ] && echo "HARNESS_RESULT: PASS" || echo "HARNESS_RESULT: FAIL"
exit $FAIL
