from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple, Type, TypeVar

from annofabapi import models as afm
from annofabapi.models import JobStatus, JobType, TaskPhase, TaskStatus
from dataclasses_json import DataClassJsonMixin

E = TypeVar("E", bound=Enum)


def _decode_enum(enum: Type[E], value: Any) -> E:
    for e in enum:
        if e == value:
            return e

    raise ValueError("{}は有効な、{}型の値ではありません".format(value, enum.__name__))


@dataclass
class Label(DataClassJsonMixin):
    label_id: str
    ja_name: str
    en_name: str
    color: Tuple[int, int, int]
    metadata: Dict[str, str]


@dataclass
class Project(DataClassJsonMixin):
    project_id: str
    organization_id: str
    title: str
    project_status: str
    input_data_type: str
    created_datetime: str
    updated_datetime: str
    overview: str

    @classmethod
    def decode(cls, project: afm.Project) -> "Project":
        return Project(
            project_id=project["project_id"],
            organization_id=project["organization_id"],
            title=project["title"],
            project_status=project["project_status"],
            input_data_type=project["input_data_type"],
            created_datetime=project["created_datetime"],
            updated_datetime=project["updated_datetime"],
            overview=project["overview"],
        )


@dataclass
class JobInfo(DataClassJsonMixin):
    project_id: str
    job_type: JobType
    job_id: str
    job_status: JobStatus
    created_datetime: str
    updated_datetime: str

    @classmethod
    def decode(cls, info: afm.JobInfo) -> "JobInfo":
        return JobInfo(
            project_id=info["project_id"],
            job_type=_decode_enum(JobType, info["job_type"]),
            job_id=info["job_id"],
            job_status=_decode_enum(JobStatus, info["job_status"]),
            created_datetime=info["created_datetime"],
            updated_datetime=info["updated_datetime"],
        )


@dataclass
class TaskGenerateResponse(DataClassJsonMixin):
    project: Project
    job: JobInfo


@dataclass
class TaskHistoryShort:
    phase: TaskPhase
    phase_stage: int
    account_id: str
    worked: bool

    @classmethod
    def decode(cls, history: afm.TaskHistoryShort) -> "TaskHistoryShort":
        return TaskHistoryShort(
            phase=_decode_enum(TaskPhase, history["phase"]),
            phase_stage=history["phase_stage"],
            account_id=history["account_id"],
            worked=history["worked"],
        )

    @classmethod
    def decode_many(cls, histories: List[afm.TaskHistoryShort]) -> List["TaskHistoryShort"]:
        return [cls.decode(h) for h in histories]


@dataclass
class Task(DataClassJsonMixin):
    project_id: str
    task_id: str
    phase: TaskPhase
    phase_stage: int
    status: TaskStatus
    input_data_id_list: List[str]
    account_id: str
    histories_by_phase: List[TaskHistoryShort]
    work_time_span: int
    number_of_rejections: int
    started_datetime: str
    updated_datetime: str
    sampling: str

    @classmethod
    def decode(cls, task: afm.Task) -> "Task":
        return Task(
            project_id=task["project_id"],
            task_id=task["task_id"],
            phase=task["phase"],
            phase_stage=task["phase_stage"],
            status=task["status"],
            input_data_id_list=task["input_data_id_list"],
            account_id=task["account_id"],
            histories_by_phase=TaskHistoryShort.decode_many(task["histories_by_phase"]),
            work_time_span=task["work_time_span"],
            number_of_rejections=task["number_of_rejections"],
            started_datetime=task["started_datetime"],
            updated_datetime=task["updated_datetime"],
            sampling=task["sampling"],
        )


@dataclass
class XYZ:
    x: float
    y: float
    z: float


@dataclass
class Size:
    width: float
    height: float
    depth: float


@dataclass
class CuboidShape(DataClassJsonMixin):
    """
    Args:
        rotation: EulerAngle での回転角。 適用順は z -> x -> y
    """

    dimensions: Size
    location: XYZ
    rotation: XYZ


@dataclass
class CuboidAnnotationDetailData(DataClassJsonMixin):
    shape: CuboidShape
    kind: str = "CUBOID"


@dataclass
class CuboidAnnotationDetail(DataClassJsonMixin):
    annotation_id: str
    account_id: str
    label_id: str
    is_protected: bool
    data: List[CuboidAnnotationDetailData]
    data_holding_type: str = "inner"
