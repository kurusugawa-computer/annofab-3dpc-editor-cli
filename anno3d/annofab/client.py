from contextlib import contextmanager
from typing import Generator, Optional

import annofabapi
from annofabapi import AnnofabApi, Resource


class ClientLoader:
    """
    Raises:
        ValueError: 「`annofab_pat`がNone」 AND 「`annofab_id` OR `annofab_pass`がNone」のとき
    """

    _annofab_id: Optional[str]
    _annofab_pass: Optional[str]
    _annofab_pat: Optional[str]
    _annofab_endpoint: Optional[str]

    def __init__(
        self,
        annofab_id: Optional[str],
        annofab_pass: Optional[str],
        annofab_pat: Optional[str],
        endpoint: Optional[str],
    ) -> None:
        if annofab_pass is None and (annofab_id is None or annofab_pass is None):
            raise ValueError("以下のいずれかの条件を満たす必要があります。(A) 'annofab_pat'を指定する。 (B) 'annofab_id'と'annofab_pass'の両方を指定する。")

        self._annofab_id = annofab_id
        self._annofab_pass = annofab_pass
        self._annofab_pat = annofab_pat
        self._annofab_endpoint = endpoint

    @contextmanager
    def open_resource(self) -> Generator[Resource, None, None]:
        endpoint = (
            self._annofab_endpoint if self._annofab_endpoint is not None else annofabapi.resource.DEFAULT_ENDPOINT_URL
        )
        resource = annofabapi.build(
            self._annofab_id,
            self._annofab_pass,
            self._annofab_pat,
            endpoint_url=endpoint,
        )
        try:
            yield resource
        finally:
            resource.api.session.close()

    @contextmanager
    def open_api(self) -> Generator[AnnofabApi, None, None]:
        with self.open_resource() as r:
            yield r.api
