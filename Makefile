.PHONY: proto proto-stubs publish-stubs

proto:
	uv run python -m grpc_tools.protoc \
		-I proto \
		--python_out=src \
		--grpc_python_out=src \
		--pyi_out=src \
		proto/ecom_agent/v1/agent.proto

proto-stubs:
	uv run python -m grpc_tools.protoc \
		-I proto \
		--python_out=stub-package/src \
		--grpc_python_out=stub-package/src \
		--pyi_out=stub-package/src \
		proto/ecom_agent/v1/agent.proto

publish-stubs: proto-stubs
	cd stub-package && uv build && uv publish
