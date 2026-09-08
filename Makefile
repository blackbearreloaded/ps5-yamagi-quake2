SHELL := bash
.DEFAULT_GOAL := help

PS5_NATIVE_APP_TEMPLATE ?= $(abspath .deps/native-app)
PS5_PAYLOAD_SDK ?= $(PS5_NATIVE_APP_TEMPLATE)/.deps/native/ps5-payload-sdk
PS5_OPENGL_PREFIX ?= $(abspath .deps/game-sdk)
export PS5_NATIVE_APP_TEMPLATE PS5_PAYLOAD_SDK PS5_OPENGL_PREFIX

.PHONY: help deps check smoke contract test native app package ffpfsc demo
help:
	@printf '%s\n' 'check: verify the frozen SDK, source pin and native helper bytes (offline)' \
	  'smoke: compile/link the existing EGL/OpenGL consumer and compile native helpers (offline)' \
	  'native: build the staged Yamagi PS5 app with static GL3/EGL and PacBrew SDL2.'
	@printf '%s\n' 'deps: restore pinned build dependencies' 'test: run host regressions' 'package: build a ready-to-run demo ZIP'
	@printf '%s\n' 'ffpfsc: build the ZIP and a verified compressed FFPFSC image'

deps:
	python3 tools/bootstrap.py

check:
	bash tools/check.sh

smoke: check
	$(MAKE) --no-print-directory -f tests/Makefile

test: contract

contract:
	python3 tests/ps5_contract.py
	python3 tests/test_lifecycle.py
	python3 tests/test_video_size.py
	python3 tests/test_game_data.py
	python3 tests/test_realpath.py
	python3 tests/test_native_resolver.py
	python3 tests/test_input_saves.py
	python3 tests/test_fps_profile.py
	python3 tests/test_triangle_path.py
	python3 tests/test_particles.py
	python3 tests/test_menu_audio.py
	python3 tests/check_gamepad_defaults.py
	python3 tests/test_package.py

app: native

native: check contract
	bash tools/build-ps5.sh

demo:
	python3 tools/prepare-demo.py --download --destination .deps/demo-baseq2

package: native demo
	python3 tools/package.py --stage build/ps5-native-fixed/dist/PPSA99007

ffpfsc: package
	rm -f -- dist/PPSA99007.ffpfsc
	@mkpfs=$$(bash "$(PS5_NATIVE_APP_TEMPLATE)/tools/setup-packaging-dependencies.sh" ffpfsc) && \
	  "$$mkpfs" pack folder --no-adjust-output-file-extension --version PS5 --verify dist/PPSA99007 dist/PPSA99007.ffpfsc && \
	  "$$mkpfs" unpack --deep --overwrite --no-progress dist/PPSA99007.ffpfsc build/ffpfsc-roundtrip
	diff -qr dist/PPSA99007 build/ffpfsc-roundtrip
	python3 tests/check_game_data.py build/ffpfsc-roundtrip/assets/baseq2
	cd dist && sha256sum PPSA99007.ffpfsc > PPSA99007.ffpfsc.sha256
