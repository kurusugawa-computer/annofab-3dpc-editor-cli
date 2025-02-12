import os

import pytest

from anno3d.annofab.client import IdPass, Pat
from anno3d.app import InvalidCredentialError, get_annofab_credential


class Test_get_annofab_credential:
    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ.pop("ANNOFAB_USER_ID", None)
        os.environ.pop("ANNOFAB_PASSWORD", None)
        os.environ.pop("ANNOFAB_PAT", None)

    def test_コマンドライン引数で指定されたパーソナルアクセストークンの優先順位は1番目(
        self,
    ):
        os.environ["ANNOFAB_USER_ID"] = "env_user_id"
        os.environ["ANNOFAB_PAT"] = "env_pat"
        credential = get_annofab_credential(
            cli_annofab_id="cli_user_id",
            cli_annofab_pass="cli_password",
            cli_annofab_pat="cli_pat",
        )
        assert isinstance(credential, Pat)
        assert credential.token == "cli_pat"

    def test_コマンドライン引数で指定されたユーザーIDの優先順位は2番目(
        self,
    ):
        os.environ["ANNOFAB_USER_ID"] = "env_user_id"
        os.environ["ANNOFAB_PAT"] = "env_pat"
        credential = get_annofab_credential(
            cli_annofab_id="cli_user_id",
            cli_annofab_pass="cli_password",
            cli_annofab_pat=None,
        )
        assert isinstance(credential, IdPass)
        assert credential.user_id == "cli_user_id"
        assert credential.password == "cli_password"

    def test_環境変数で指定されたパーソナルアクセストークンの優先順位は3番目(
        self,
    ):
        os.environ["ANNOFAB_USER_ID"] = "env_user_id"
        os.environ["ANNOFAB_PAT"] = "env_pat"
        credential = get_annofab_credential(
            cli_annofab_id=None,
            cli_annofab_pass="cli_password",
            cli_annofab_pat=None,
        )
        assert isinstance(credential, Pat)
        assert credential.token == "env_pat"

    def test_環境変数で指定されたユーザーIDの優先順位は4番目(
        self,
    ):
        os.environ["ANNOFAB_USER_ID"] = "env_user_id"
        credential = get_annofab_credential(
            cli_annofab_id=None,
            cli_annofab_pass="cli_password",
            cli_annofab_pat=None,
        )
        assert isinstance(credential, IdPass)
        assert credential.user_id == "env_user_id"
        assert credential.password == "cli_password"

    def test_コマンドライン引数で指定されたパスワードは環境変数で指定されたパスワードより優先順位が高い(
        self,
    ):
        os.environ["ANNOFAB_PASSWORD"] = "env_password"
        credential = get_annofab_credential(
            cli_annofab_id="cli_user_id",
            cli_annofab_pass="cli_password",
            cli_annofab_pat=None,
        )
        assert isinstance(credential, IdPass)
        assert credential.user_id == "cli_user_id"
        assert credential.password == "cli_password"

    def test_環境変数で指定されたパスワードが参照されること(
        self,
    ):
        os.environ["ANNOFAB_PASSWORD"] = "env_password"
        credential = get_annofab_credential(
            cli_annofab_id="cli_user_id",
            cli_annofab_pass=None,
            cli_annofab_pat=None,
        )
        assert isinstance(credential, IdPass)
        assert credential.user_id == "cli_user_id"
        assert credential.password == "env_password"

    def test_コマンドライン引数でユーザーIDが指定されている状態でパスワードが指定されないとInvalidCredentialErrorがraiseされる(  # noqa: E501
        self,
    ):
        with pytest.raises(InvalidCredentialError):
            get_annofab_credential(
                cli_annofab_id="cli_user_id",
                cli_annofab_pass=None,
                cli_annofab_pat=None,
            )

    def test_環境変数でユーザーIDが指定されている状態でパスワードが指定されないとInvalidCredentialErrorがraiseされる(
        self,
    ):
        os.environ["ANNOFAB_USER_ID"] = "env_user_id"
        with pytest.raises(InvalidCredentialError):
            get_annofab_credential(
                cli_annofab_id=None,
                cli_annofab_pass=None,
                cli_annofab_pat=None,
            )

    def test_ユーザーIDとパーソナルアクセストークンの両方が指定されていないとInvalidCredentialErrorがraiseされる(
        self,
    ):
        with pytest.raises(InvalidCredentialError):
            get_annofab_credential(
                cli_annofab_id=None,
                cli_annofab_pass=None,
                cli_annofab_pat=None,
            )
