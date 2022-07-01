from contextlib import contextmanager
from typing import Generator, Optional

import annofabapi
from annofabapi import AnnofabApi, Resource


class ClientLoader:
    _annofab_id: str
    _annofab_pass: str
    _annofab_endpoint: Optional[str]

    def __init__(self, annofab_id: str, annofab_pass: str, endpoint: Optional[str]) -> None:
        self._annofab_id = annofab_id
        self._annofab_pass = annofab_pass
        self._annofab_endpoint = endpoint

    @contextmanager
    def open_resource(self) -> Generator[Resource, None, None]:
        endpoint = (
            self._annofab_endpoint if self._annofab_endpoint is not None else annofabapi.resource.DEFAULT_ENDPOINT_URL
        )
        resource = annofabapi.build(self._annofab_id, self._annofab_pass, endpoint)
        try:
            yield resource
        finally:
            resource.api.session.close()

    @contextmanager
    def open_api(self) -> Generator[AnnofabApi, None, None]:
        with self.open_resource() as r:
            yield r.api
