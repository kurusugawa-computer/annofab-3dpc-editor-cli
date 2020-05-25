from contextlib import contextmanager
from typing import Generator

import annofabapi
from annofabapi import AnnofabApi, Resource


class ClientLoader:
    _annofab_id: str
    _annofab_pass: str

    def __init__(self, annofab_id: str, annofab_pass: str) -> None:
        self._annofab_id = annofab_id
        self._annofab_pass = annofab_pass

    @contextmanager
    def open_resource(self) -> Generator[Resource]:
        resource = annofabapi.build(self._annofab_id, self._annofab_pass)
        try:
            yield resource
        finally:
            resource.api.session.close()

    @contextmanager
    def open_api(self) -> Generator[AnnofabApi]:
        with self.open_resource() as r:
            yield r.api
