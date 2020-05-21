def frame_meta(input_data_id: str) -> str:
    return f"{input_data_id}.meta"


def camera_image(input_data_id: str, number: int) -> str:
    return f"{input_data_id}.camera_{number}"


def camera_image_calib(input_data_id: str, number: int) -> str:
    return f"{camera_image(input_data_id, number)}.calib"
