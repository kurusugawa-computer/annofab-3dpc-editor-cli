def frame_meta_id(input_data_id: str) -> str:
    return f"{input_data_id}.meta"


def camera_image_id(input_data_id: str, number: int) -> str:
    return f"{input_data_id}.camera_{number}"


def camera_image_calib_id(input_data_id: str, number: int) -> str:
    return f"{camera_image_id(input_data_id, number)}.calib"
