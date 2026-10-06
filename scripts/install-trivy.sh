#!/bin/sh
# Verified release assets; no floating install script or third-party action.
set -eu
version=0.75.0
case "$(uname -m)" in
  x86_64) arch=64bit; checksum=c6e65abddb348e25f10549df887045629cf28cc72453cd1c63acb717316b3f3f ;;
  aarch64|arm64) arch=ARM64; checksum=a1ee9f6ffb7d112b64ff726a2a0717c21175c1114361391f4a132956751a13b3 ;;
  *) echo 'Unsupported scanner architecture' >&2; exit 1 ;;
esac
[ "$(uname -s)" = Linux ] || { echo 'Scanner installation requires Linux' >&2; exit 1; }
destination="${TRIVY_BIN_DIR:-.tools/trivy}"
mkdir -p "$destination"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
asset="trivy_${version}_Linux-${arch}.tar.gz"
curl --fail --location --silent --show-error --retry 3 --max-time 180 \
  "https://github.com/aquasecurity/trivy/releases/download/v${version}/${asset}" \
  -o "$temporary/$asset"
printf '%s  %s\n' "$checksum" "$temporary/$asset" | sha256sum --check
tar -xzf "$temporary/$asset" -C "$destination" trivy
"$destination/trivy" --version
