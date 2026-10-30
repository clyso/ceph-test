#!/usr/bin/env bash
# Usage: health-check.sh <image>
# Starts the image with every optional component enabled and waits until
# ceph-test-health reports all of them ready. The entrypoint stops the
# container if a daemon dies or a setup step fails, which ends the wait early.
set -euo pipefail

IMAGE=$1
NAME=ceph-health-test
TIMEOUT=300

trap 'docker rm -f "$NAME" >/dev/null 2>&1 || true' EXIT
docker rm -f "$NAME" >/dev/null 2>&1 || true

docker run -d --name "$NAME" \
  -e CEPH_DEMO_ACCESS_KEY=testkey \
  -e CEPH_DEMO_SECRET_KEY=testsecret \
  -e CEPH_RGW_SEED=true \
  -e CEPH_RBD_POOL=rbd \
  -e CEPH_CEPHFS=true \
  -e CEPH_DEVICE_CLASS=hdd \
  -e CEPH_TEST_ORCHESTRATOR=true \
  -e CEPH_PROMETHEUS=true \
  -e CEPH_DASHBOARD=true \
  "$IMAGE" >/dev/null

start=$SECONDS
until docker exec "$NAME" ceph-test-health all >/dev/null 2>&1; do
  if [ "$(docker inspect -f '{{.State.Running}}' "$NAME")" != true ] \
    || [ $((SECONDS - start)) -ge "$TIMEOUT" ]; then
    echo "FAILED: not ready after $((SECONDS - start))s"
    docker logs "$NAME"
    exit 1
  fi
  sleep 2
done
echo "All components ready after $((SECONDS - start))s"
