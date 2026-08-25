from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("annofab-3dpc-editor-cli")
except PackageNotFoundError:
    # ソースツリーから直接実行した場合は、配布メタデータが存在しない。
    __version__ = "0.0.0"
