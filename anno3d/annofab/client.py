from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Optional, Union

import annofabapi
from annofabapi import AnnofabApi, Resource

from anno3d.util.type_util import assert_noreturn


@dataclass(frozen=True)
class IdPass:
    """ユーザIDとパスワード"""

    user_id: str
    password: str


@dataclass(frozen=True)
class Pat:
    """Personal Access Token"""

    token: str


Credential = Union[IdPass, Pat]


class ClientLoader:
    _credential: Credential

    def __init__(
        self,
        credential: Credential,
        endpoint: Optional[str],
    ) -> None:
        self._credential = credential
        self._annofab_endpoint = endpoint

    @contextmanager
    def open_resource(self) -> Generator[Resource, None, None]:
        endpoint = (
            self._annofab_endpoint if self._annofab_endpoint is not None else annofabapi.resource.DEFAULT_ENDPOINT_URL
        )
        annofab_id = None
        annofab_pass = None
        annofab_pat = None
        if isinstance(self._credential, IdPass):
            annofab_id = self._credential.user_id
            annofab_pass = self._credential.password
        elif isinstance(self._credential, Pat):
            annofab_pat = self._credential.token
        else:
            assert_noreturn(self._credential)

        resource = annofabapi.build(
            annofab_id,
            annofab_pass,
            annofab_pat,
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
