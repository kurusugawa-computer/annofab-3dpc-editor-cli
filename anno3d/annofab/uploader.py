import abc
import logging
import mimetypes
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from enum import Enum
from http import HTTPStatus
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional

import boto3
import more_itertools
import requests
from annofabapi import AnnofabApi
from annofabapi import Wrapper as AnnofabApiWrapper
from botocore.errorfactory import ClientError
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)


@dataclass(frozen=True)
class DataPath:
    url: str
    path: str


logger = logging.getLogger(__name__)


class UploadErrorType(Enum):
    """一時ストレージのアップロード失敗の、正規化済みの種別。"""

    HTTP = "http"
    S3_REQUEST_TIMEOUT = "s3_request_timeout"
    CONNECTION = "connection"
    TIMEOUT = "timeout"
    OTHER = "other"


def _is_retryable_http_status_code(status_code: int) -> bool:
    """再試行可能なHTTPステータスコードかを返す。"""
    retryable_status_codes = frozenset(
        {
            HTTPStatus.REQUEST_TIMEOUT,
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        }
    )
    return status_code in retryable_status_codes


class UploadRequestError(Exception):
    """署名付きURLを含まない、一時ストレージへのアップロード失敗を表す基底例外。"""

    error_type: ClassVar[UploadErrorType]

    def __init__(self) -> None:
        super().__init__(f"Temporary storage upload failed: status={self.status_code}, type={self.error_type.value}")

    @property
    def status_code(self) -> Optional[int]:
        """HTTP応答のステータスコード。HTTP応答がない場合はNone。"""
        return None

    @property
    def retry_after_seconds(self) -> Optional[float]:
        """Retry-Afterヘッダから解析済みの待機秒数。HTTP応答以外ではNone。"""
        return None

    @property
    def retryable(self) -> bool:
        """この失敗を再試行するか。"""
        return False


class HttpUploadRequestError(UploadRequestError):
    """HTTP応答を受けた一時ストレージへのアップロード失敗。"""

    error_type = UploadErrorType.HTTP

    def __init__(self, status_code: int, retry_after_seconds: Optional[float]) -> None:
        if retry_after_seconds is not None and retry_after_seconds < 0:
            raise ValueError("Retry-After must not be negative")
        self._status_code = status_code
        self._retry_after_seconds = retry_after_seconds
        super().__init__()

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def retry_after_seconds(self) -> Optional[float]:
        return self._retry_after_seconds

    @property
    def retryable(self) -> bool:
        return _is_retryable_http_status_code(self.status_code)


class S3RequestTimeoutUploadRequestError(HttpUploadRequestError):
    """S3のHTTP 400 / RequestTimeout 応答によるアップロード失敗。"""

    error_type = UploadErrorType.S3_REQUEST_TIMEOUT

    def __init__(self, retry_after_seconds: Optional[float]) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, retry_after_seconds)

    @property
    def retryable(self) -> bool:
        return True


class ConnectionUploadRequestError(UploadRequestError):
    """接続エラーによるアップロード失敗。"""

    error_type = UploadErrorType.CONNECTION

    @property
    def retryable(self) -> bool:
        return True


class TimeoutUploadRequestError(UploadRequestError):
    """タイムアウトによるアップロード失敗。"""

    error_type = UploadErrorType.TIMEOUT

    @property
    def retryable(self) -> bool:
        return True


class OtherUploadRequestError(UploadRequestError):
    """再試行しないその他のアップロード失敗。"""

    error_type = UploadErrorType.OTHER


def _to_upload_request_error(error: requests.exceptions.RequestException) -> UploadRequestError:
    """requests例外から、URLを保持しないアップロード例外を作成する。

    Args:
        error: 一時ストレージへのアップロードで発生したrequests例外。

    Returns:
        再試行判定に必要な情報だけを保持する例外。
    """
    if isinstance(error, requests.exceptions.HTTPError) and error.response is not None:
        response = error.response
        retry_after_seconds = (
            _parse_retry_after_seconds(response.headers["Retry-After"]) if "Retry-After" in response.headers else None
        )
        if _is_s3_request_timeout_response(response):
            return S3RequestTimeoutUploadRequestError(retry_after_seconds)
        return HttpUploadRequestError(response.status_code, retry_after_seconds)

    if isinstance(error, requests.exceptions.ConnectionError):
        return ConnectionUploadRequestError()
    if isinstance(error, requests.exceptions.Timeout):
        return TimeoutUploadRequestError()
    return OtherUploadRequestError()


def _get_retry_after_seconds(error: UploadRequestError) -> Optional[float]:
    """再試行可能な応答の Retry-After を秒数へ変換する。

    Args:
        error: リトライ対象となった例外。

    Returns:
        有効な Retry-After の待機秒数。取得できない場合はNone。
    """
    return error.retry_after_seconds


def _parse_retry_after_seconds(retry_after: str, now: Optional[datetime] = None) -> Optional[float]:
    """Retry-After ヘッダ値を秒数へ変換する。

    Args:
        retry_after: Retry-After ヘッダの値。
        now: HTTP-date 形式を秒数に変換する際の基準時刻。None の場合は現在時刻を使用する。

    Returns:
        有効な Retry-After の待機秒数。値が不正な場合はNone。
    """
    retry_after = retry_after.strip()
    if retry_after.isascii() and retry_after.isdigit():
        return float(retry_after)

    try:
        retry_at = parsedate_to_datetime(retry_after)
    except (IndexError, OverflowError, TypeError, ValueError):
        return None

    if retry_at.tzinfo is None:
        return None

    if now is None:
        now = datetime.now(timezone.utc)
    return max(0.0, (retry_at - now).total_seconds())


def _wait_upload_retry(retry_state: RetryCallState) -> float:
    """Retry-After と指数バックオフのうち長い方を待機時間として返す。

    Args:
        retry_state: Tenacity が再試行ごとに渡す状態。

    Returns:
        次回の再試行までの待機秒数。
    """
    exponential_wait = wait_random_exponential(multiplier=1, max=30)(retry_state)
    if retry_state.outcome is None:
        return exponential_wait

    error = retry_state.outcome.exception()
    if error is None:
        return exponential_wait

    if not isinstance(error, UploadRequestError):
        return exponential_wait

    retry_after = _get_retry_after_seconds(error)
    if retry_after is None:
        return exponential_wait
    return max(exponential_wait, retry_after)


def _is_s3_request_timeout_response(response: requests.Response) -> bool:
    """S3のHTTP 400 / RequestTimeout応答かを返す。

    Args:
        response: 判定対象のHTTPレスポンス。

    Returns:
        HTTPステータスが400で、レスポンスXMLのエラーコードが
        ``RequestTimeout`` の場合はTrue。それ以外の場合はFalse。

    Examples:
        以下のようなS3エラー応答を判定する。

        .. code-block:: xml

            <Error>
                <Code>RequestTimeout</Code>
                <Message>Your socket connection timed out.</Message>
            </Error>
    """
    if response.status_code != HTTPStatus.BAD_REQUEST:
        return False

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return False

    if root.tag != "Error":
        return False

    for child in root:
        if child.tag == "Code":
            return child.text == "RequestTimeout"

    return False


def _is_retryable_upload_error(error: BaseException) -> bool:
    """一時的な通信エラー、または再試行可能なHTTPエラーかを返す。

    Args:
        error: 判定対象の例外。

    Returns:
        再試行可能な場合はTrue。それ以外の場合はFalse。
    """
    return isinstance(error, UploadRequestError) and error.retryable


def _log_upload_retry(retry_state: RetryCallState, filename: str) -> None:
    """署名付きURLを出力せずに、アップロードの再試行を記録する。

    Args:
        retry_state: Tenacityが再試行ごとに渡す状態。
        filename: アップロード対象ファイルの名前。
    """
    error = retry_state.outcome.exception() if retry_state.outcome is not None else None
    if not isinstance(error, UploadRequestError):
        return

    logger.warning(
        "Retrying temporary storage upload: file=%s, status=%s, type=%s, attempt=%d",
        filename,
        error.status_code,
        error.error_type.value,
        retry_state.attempt_number,
    )


def _get_content_type(upload_file: Path) -> str:
    """
    アップロードするファイルのContent-Typeを取得する。
    """
    content_type, _ = mimetypes.guess_type(upload_file)
    if content_type is None:
        # ファイル名から推測できない場合
        return "application/octet-stream"
    return content_type


class Uploader(abc.ABC):
    """

    Args:
        client:
        project: プロジェクトID
        force: 入力データと補助データを上書きしてアップロードするかどうか。
    """

    _client: AnnofabApi
    _project: str

    def __init__(self, client: AnnofabApi, project: str, force: bool = False):
        self._client = client
        self._client_wrapper = AnnofabApiWrapper(client)
        self._project = project
        self._force = force

    def get_input_data(self, input_data_id: str) -> Optional[Any]:
        return self._client_wrapper.get_input_data_or_none(self._project, input_data_id)

    @abc.abstractmethod
    def upload_tempdata(self, upload_file: Path, *, content_type: Optional[str] = None) -> str:
        pass

    def upload_input_data(self, input_data_id: str, file: Path, *, content_type: Optional[str] = None) -> str:
        path = self.upload_tempdata(file, content_type=content_type)

        data_id = input_data_id
        body = {"input_data_name": file.name, "input_data_path": path}
        if self._force:
            old_input_data = self.get_input_data(input_data_id)
            if old_input_data is not None:
                body["last_updated_datetime"] = old_input_data["updated_datetime"]

        input_data, _ = self._client.put_input_data(self._project, data_id, query_params=None, request_body=body)

        logger.debug("uploaded input data: %s", input_data)
        return data_id

    def upload_supplementary(
        self,
        input_data_id: str,
        supplementary_id: str,
        file: Path,
        supplementary_data_type: Literal["custom", "image", "text"],
        *,
        content_type: Optional[str] = None,
    ) -> str:
        path = self.upload_tempdata(file, content_type=content_type)
        body = {
            "supplementary_data_name": supplementary_id,
            "supplementary_data_path": path,
            "supplementary_data_type": supplementary_data_type,
            "supplementary_data_number": 0,
        }
        if self._force:
            supplementary_list, _ = self._client.get_supplementary_data_list(self._project, input_data_id)
            old_supplementary = more_itertools.first_true(
                supplementary_list, pred=lambda e: e["supplementary_data_id"] == supplementary_id
            )
            if old_supplementary is not None:
                body["last_updated_datetime"] = old_supplementary["updated_datetime"]

        supplementary, _ = self._client.put_supplementary_data(self._project, input_data_id, supplementary_id, body)
        logger.debug("uploaded supplementary data: %s", supplementary)
        return supplementary_id


class AnnofabStorageUploader(Uploader):
    def upload_tempdata(self, upload_file: Path, *, content_type: Optional[str] = None) -> str:
        """
        ファイルをAnnofabストレージ（AWS S3）にアップロードします。

        Args:
            upload_file: アップロードするファイル
            content_type: アップロードするファイルのContent-Type。Noneの場合はファイル名から推測します。

        Returns:
            アップロードしたファイルのS3 URI
        """
        client = self._client

        data_path_dict, _ = client.create_temp_path(self._project)

        data_path = DataPath(data_path_dict["url"], data_path_dict["path"])
        if content_type is None:
            content_type = _get_content_type(upload_file)

        # 一時的な通信エラーでは最大5回、指数バックオフでアップロードを再試行する。
        # requests例外は署名付きURLを含まない例外へ変換してからTenacityへ渡す。
        @retry(
            retry=retry_if_exception(_is_retryable_upload_error),
            stop=stop_after_attempt(5),
            wait=_wait_upload_retry,
            before_sleep=lambda retry_state: _log_upload_retry(retry_state, upload_file.name),
            reraise=True,
        )
        def upload() -> None:
            try:
                # 再試行時にもファイルを先頭から送信する。
                with upload_file.open(mode="rb") as data:
                    response = requests.put(
                        data_path.url,
                        data=data,
                        headers={"Content-Type": content_type},
                        timeout=600,
                    )
                response.raise_for_status()
            except requests.exceptions.RequestException as error:
                # ``from None`` により、HTTPError（URLを含む）を例外チェーンへ残さない。
                raise _to_upload_request_error(error) from None

        upload()

        return data_path.path


class S3Uploader(Uploader):
    """
    AWS S3にファイルをアップロードした上で、Annofabに入力データや補助情報を登録するクラス。
    """

    def __init__(self, client: AnnofabApi, project: str, s3_path: str, force: bool = False):
        tmp = s3_path.split("/")
        self._s3_bucket = tmp[0]
        s3_prefix_key = s3_path[len(self._s3_bucket + "/") :]
        if not s3_prefix_key.endswith("/"):
            s3_prefix_key += "/"
        self._s3_prefix_key = s3_prefix_key
        self._s3_client = boto3.client("s3")
        super().__init__(client=client, project=project, force=force)

    def s3_key_exists(self, key: str) -> bool:
        try:
            self._s3_client.head_object(Bucket=self._s3_bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_s3_uri(self, key: str) -> str:
        return f"s3://{self._s3_bucket}/{key}"

    def upload_tempdata(self, upload_file: Path, *, content_type: Optional[str] = None) -> str:
        """
        ファイルをAWS S3にアップロードします。

        Args:
            upload_file: アップロードするファイル
            content_type: アップロードするファイルのContent-Type。Noneの場合はファイル名から推測します。

        Returns:
            アップロードしたファイルのS3 URI
        """
        client = self._s3_client
        key = self._s3_prefix_key + f"{upload_file.parent.name}/{upload_file.name}"

        if self._force or not self.s3_key_exists(key):
            if content_type is None:
                content_type = _get_content_type(upload_file)
            client.upload_file(
                Filename=str(upload_file), Bucket=self._s3_bucket, Key=key, ExtraArgs={"ContentType": content_type}
            )
            return self.get_s3_uri(key)
        else:
            raise RuntimeError(f"AWS S3にオブジェクトがすでに存在します。Bucket='{self._s3_bucket}', Key='{key}'")
