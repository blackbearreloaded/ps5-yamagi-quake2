#!/usr/bin/env bash
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
template=${PS5_NATIVE_APP_TEMPLATE:-"$root/.deps/native-app"}
prefix=${PS5_OPENGL_PREFIX:-"$root/.deps/game-sdk"}
patch_file="$root/patches/0001-ps5-static-gl3-lifecycle.patch"
# Build in an isolated stage; dependencies and the upstream checkout stay intact.
stage="$root/build/ps5-native-fixed"

[[ -f "$template/Makefile" && -f "$template/tools/build.sh" ]] || {
	printf 'missing PS5 native-app boilerplate: %s\n' "$template" >&2
	exit 2
}
[[ $(git -C "$template" rev-parse HEAD) == 722f2227a8bb6fa2229120546995b6562552c752 ]]
git -C "$template" diff --exit-code HEAD -- >/dev/null
[[ -x "$template/.deps/native/ps5-payload-sdk/bin/prospero-lld" ]] || {
	printf 'missing cached PS5 payload SDK under %s/.deps/native\n' "$template" >&2
	exit 2
}
(cd "$prefix" && sha256sum --check --strict manifest.sha256 >/dev/null)
git -C "$root/upstream/yquake2" apply --check "$patch_file"
test -s "$root/src/ps5/ps5_main.c"

[[ $(realpath -m -- "$stage") == "$root/build/ps5-native-fixed" ]] || exit 2
rm -rf -- "$stage"
mkdir -p "$stage/.deps"
cp "$template/Makefile" "$stage/Makefile"
for directory in assets runtime sce_sys tooling tools; do
	mkdir -p "$stage/$directory"
	cp -a "$template/$directory/." "$stage/$directory/"
done
# The tested RELRO alignment fix is kept here until published upstream.
(cd "$stage" && patch --batch --fuzz=0 -p1 -i "$root/patches/0003-native-relro-alignment.patch")
# Import stubs below must be written only into this build's own SDK copy.
cp -a "$template/.deps/native" "$stage/.deps/native"
mkdir -p "$root/.deps/pacbrew"
ln -s "$root/.deps/pacbrew" "$stage/.deps/pacbrew"
mkdir -p "$stage/upstream/yquake2"
cp -a "$root/upstream/yquake2/." "$stage/upstream/yquake2/"
git -C "$stage/upstream/yquake2" apply "$patch_file"

rm -rf -- "$stage/src"
mkdir -p "$stage/src"
cp -a "$stage/upstream/yquake2/src/." "$stage/src/"
rm -rf -- \
	"$stage/src/backends/windows" \
	"$stage/src/client/refresh/gl1" \
	"$stage/src/client/refresh/soft" \
	"$stage/src/client/refresh/gl3/glad-gles3"
rm -f -- \
	"$stage/src/backends/unix/main.c" \
	"$stage/src/win-wrapper/wrapper.c" \
	"$stage/src/client/input/sdl3.c" \
	"$stage/src/client/vid/glimp_sdl2.c" \
	"$stage/src/client/vid/glimp_sdl3.c" \
	"$stage/src/client/refresh/gl3/gl3_sdl.c"
mkdir -p "$stage/src/ps5"
cp -a "$root/src/ps5/." "$stage/src/ps5/"

rm -rf -- "$stage/include"
mkdir -p "$stage/include"
cp -a "$prefix/include/." "$stage/include/"
cp -a "$root/assets/." "$stage/assets/"
cp -a "$root/sce_sys/." "$stage/sce_sys/"
bash "$template/tools/validate-assets.sh" "$stage/sce_sys"
cp "$root/tooling/native/app_heap.c" "$stage/src/app_heap.c"
cp "$root/tooling/native/runtime_shims.c" "$stage/src/runtime_shims.c"
cp "$root/tooling/native/app-symbols.map" "$stage/tooling/native/app-symbols.map"
cp "$stage/tooling/native/ps5-pie.ld" "$stage/tooling/native/ps5-pie-base.ld"
cp "$root/tooling/native/ps5-pie.ld" "$stage/tooling/native/ps5-pie.ld"

heap_default='write_u64(result.data, result.heap_size, std::numeric_limits<std::uint64_t>::max());'
test "$(grep -Fc "$heap_default" "$stage/tooling/native/sce_module_writer.cpp")" = 1
sed -i "s/$heap_default/write_u64(result.data, result.heap_size, 0x10000000ULL);/" \
	"$stage/tooling/native/sce_module_writer.cpp"
test "$(grep -Fc -- '--eh-frame-hdr \' "$stage/tools/build.sh")" = 1
sed -i 's@--eh-frame-hdr \\@--eh-frame-hdr --wrap=malloc --wrap=calloc --wrap=realloc --wrap=free --wrap=posix_memalign --wrap=malloc_usable_size \\@' \
	"$stage/tools/build.sh"
test "$(grep -Fc -- 'args=("$standard" -O2 -Wall -Wextra -ffunction-sections -fdata-sections)' "$stage/tools/build.sh")" = 1
sed -i 's@args=("\$standard" -O2 -Wall -Wextra -ffunction-sections -fdata-sections)@args=("\$standard" -std=gnu11 -O2 -Wall -Wextra -ffunction-sections -fdata-sections "-DYQ2OSTYPE=\\"PS5\\"" "-DYQ2ARCH=\\"x86_64\\"")@' \
	"$stage/tools/build.sh"
test "$(grep -Fc -- '"$sdk_root/bin/prospero-lld" -T' "$stage/tools/build.sh")" = 1
sed -i 's@"\$sdk_root/bin/prospero-lld" -T@"\$sdk_root/bin/prospero-lld" -L"\$sdk_root/target/lib" -T@' \
	"$stage/tools/build.sh"

sdk="$stage/.deps/native/ps5-payload-sdk"
mkdir -p "$stage/build/native-imports"
for stub in agc_link_stub agc_driver_link_stub; do
	PS5_PAYLOAD_SDK="$sdk" sh "$stage/tooling/prospero-clang18" \
		-std=c11 -O2 -fPIC -ffunction-sections -fdata-sections \
		-c "$root/tooling/native/$stub.c" -o "$stage/build/native-imports/$stub.o"
	case "$stub" in
		agc_link_stub) soname=libSceAgc.prx; library=libSceAgc.so ;;
		agc_driver_link_stub) soname=libSceAgcDriver.prx; library=libSceAgcDriver.so ;;
	esac
	"$sdk/bin/prospero-lld" --shared -soname "$soname" \
		-o "$sdk/target/lib/$library" "$stage/build/native-imports/$stub.o"
done

mkdir -p "$stage/vendor"
compiler_runtime="$(clang-18 --print-resource-dir)/lib/linux/libclang_rt.builtins-x86_64.a"
test -s "$compiler_runtime"
{
	printf 'SEARCH_DIR("%s")\n' "$sdk/target/lib"
	printf 'SEARCH_DIR("%s")\n' "$prefix/lib"
	printf 'EXTERN(ps5_agc_gate2_run)\n'
	printf 'GROUP (\n'
	printf '  "%s"\n' "$prefix/lib/libPS5OpenGLCore33.a"
	printf '  "%s"\n' "$sdk/target/lib/libunwind.a"
	printf '  "%s"\n' "$sdk/target/lib/libc++abi.a"
	printf '  "%s"\n' "$sdk/target/lib/libc++.a"
	printf '  "%s"\n' "$compiler_runtime"
	printf ')\n'
} > "$stage/vendor/libps5_opengl_group.a"

printf '%s\n' \
	'APP_DEFINITIONS=YQ2_PS5 NO_SDL_GYRO' \
	'APP_INCLUDE_PATHS=include src/ps5 src/client/refresh/gl3/glad/include' \
	'APP_STATIC_ARCHIVES=vendor/libps5_opengl_group.a' \
	'PACBREW_PACKAGES=sdl2' > "$stage/.env"

make -C "$stage" --no-print-directory app
printf 'Built native app stage: %s\n' "$stage/dist/PPSA99007"
