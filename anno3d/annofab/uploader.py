import abc
import logging
import mimetypes
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any, Literal, Optional

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


class TempDataUploadError(RuntimeError):
    """署名付きURLを含まない一時データアップロードの失敗を表す例外。"""

    def __init__(
        self,
        *,
        file_name: str,
        reason: str,
        status_code: Optional[int],
        retryable: bool,
        retry_after_seconds: Optional[float],
    ) -> None:
        self.file_name = file_name
        self.reason = reason
        self.status_code = status_code
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds

        status = str(status_code) if status_code is not None else "network"
        super().__init__(f"temporary-data upload failed: file={file_name}, reason={reason}, status={status}")


def _get_retry_after_seconds(error: BaseException) -> Optional[float]:
    """再試行可能な応答の Retry-After を秒数へ変換する。

    Args:
        error: リトライ対象となった例外。

    Returns:
        有効な Retry-After の待機秒数。取得できない場合はNone。
    """
    if not isinstance(error, requests.exceptions.HTTPError) or error.response is None:
        return None

    response = error.response
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None

    return _parse_retry_after_seconds(retry_after)


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
    except (IndexError, TypeError, ValueError):
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

    if isinstance(error, TempDataUploadError):
        retry_after = error.retry_after_seconds
    else:
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
    retryable_http_status_codes = frozenset(
        {
            HTTPStatus.REQUEST_TIMEOUT,
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        }
    )

    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        return response is not None and (
            response.status_code in retryable_http_status_codes or _is_s3_request_timeout_response(response)
        )

    return isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))


def _to_safe_upload_error(error: requests.exceptions.RequestException, file_name: str) -> TempDataUploadError:
    """requests例外を、URLなどの認可情報を持たない例外へ変換する。"""
    response = error.response
    status_code = response.status_code if response is not None else None

    if isinstance(error, requests.exceptions.HTTPError):
        reason = "http_error"
    elif isinstance(error, requests.exceptions.Timeout):
        reason = "timeout"
    elif isinstance(error, requests.exceptions.ConnectionError):
        reason = "connection_error"
    else:
        reason = "request_error"

    return TempDataUploadError(
        file_name=file_name,
        reason=reason,
        status_code=status_code,
        retryable=_is_retryable_upload_error(error),
        retry_after_seconds=_get_retry_after_seconds(error),
    )


def _before_sleep_upload_retry(retry_state: RetryCallState) -> None:
    """安全なアップロード失敗情報だけをリトライログへ記録する。"""
    if retry_state.outcome is None:
        return

    error = retry_state.outcome.exception()
    if not isinstance(error, TempDataUploadError):
        return

    status = str(error.status_code) if error.status_code is not None else "network"
    logger.warning(
        "temporary-data upload failed (file=%s, reason=%s, status=%s, attempt=%d/5); retrying",
        error.file_name,
        error.reason,
        status,
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
        # すべて失敗した場合は、署名付きURLを含まない例外を送出する。
        @retry(
            retry=retry_if_exception(lambda error: isinstance(error, TempDataUploadError) and error.retryable),
            stop=stop_after_attempt(5),
            wait=_wait_upload_retry,
            before_sleep=_before_sleep_upload_retry,
            reraise=True,
        )
        def upload() -> None:
            # 再試行時にもファイルを先頭から送信する。
            safe_error: Optional[TempDataUploadError] = None
            with upload_file.open(mode="rb") as data:
                try:
                    response = requests.put(
                        data_path.url,
                        data=data,
                        headers={"Content-Type": content_type},
                        timeout=600,
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as error:
                    safe_error = _to_safe_upload_error(error, upload_file.name)

            # except節の外で送出することで、元のrequests例外を例外チェーンに残さない。
            if safe_error is not None:
                raise safe_error

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
