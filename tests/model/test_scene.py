import re
from pathlib import Path

from anno3d.model.scene import XYZ, CameraViewSettings, Scene


def test_decode_scene():
    json = """{
  "id_list": [  // nuScenes にならって文字列にする（not数値）
    "006497",
    "012187"
  ],
  // ディレクトリ名とそのtypeを表す．カメラ画像の場合，対となるcalibデータディレクトリを表す．
  // 当面はKITTI形式のみ（kitti_velodyne, kitti_image, kitti_label）を予定．
  "serieses": [
    {
        "type": "kitti_velodyne",
        "velodyne_dir": "velodyne"
    },
    {
        "type": "kitti_image",
        "image_dir": "image_rf",  // 例えば側方カメラ（right-front）
        "calib_dir": null,  // calibデータがない場合はnull．この場合velodyneの重畳はできない
        // 以下 "camera_view_settings" を設けた．理由は下記
        // "dummy calib data" とかのが良いだろうか？？s
        // ここに入れて良いものかどうかとか...（ここに入れるしかないんだけど)
        "camera_view_setting": {  // 3DPCE UI向けのダミー値(*option)．定義してあるならば，calibrationより優先し，この値を参照．
            "fov": 1.57,    // rad
            "direction": 0.92,  // rad(進行方向X軸が0.0)
            "position": {   // m. Velo座標系に対するカメラ位置．
                "x": -2.0,
                "y": -1.0,
                "z": 0.8
            }
        }
    },
    {
        "type": "kitti_image",
        "image_dir": "image_2",
        "calib_dir": "calib"
    },
    {
        "type": "kitti_label",
        "label_dir": "label_2",
        "image_dir": "image_2", // label_2に紐づくimageデータ
        "calib_dir": "calib"    // label_2に紐づくcalibデータ
    },
    {
        "type": "kitti_image",
        "image_dir": "image_3",
        "camera_view_setting": {}
    },
    {
        "type": "kitti_image",
        "image_dir": "image_4",
        "file_extension": "jpg"
    },
    {
        "type": "kitti_label",
        "label_dir": "label_4",
        "image_dir": "image_4",
        "calib_dir": "calib",
        "file_extension": "jpg"
    }
  ],
  // これ以外の項目はoptionとする．有ろうが無かろうが，3DPCE側は気にしない．
  "dummy": "value"
}"""
    comment_removed = "\n".join([re.sub("//.*", "", line) for line in json.split("\n")])
    scene = Scene.decode(Path("/root/"), comment_removed)
    assert len(scene.id_list) == 2
    assert scene.id_list[0] == "006497"
    assert scene.id_list[1] == "012187"
    assert scene.velodyne.velodyne_dir == "/root/velodyne"
    assert len(scene.images) == 4
    assert len(scene.labels) == 2

    image1 = scene.images[0]
    assert image1.image_dir == "/root/image_rf"
    assert image1.calib_dir is None
    assert image1.camera_view_setting is not None
    assert image1.camera_view_setting.fov == 1.57
    assert image1.camera_view_setting.direction == 0.92
    assert image1.camera_view_setting.position == XYZ(-2.0, -1.0, 0.8)
    assert image1.file_extension == "png"

    image2 = scene.images[1]
    assert image2.image_dir == "/root/image_2"
    assert image2.calib_dir == "/root/calib"
    assert image2.camera_view_setting is None
    assert image2.file_extension == "png"

    image3 = scene.images[2]
    assert image3.image_dir == "/root/image_3"
    assert image3.calib_dir is None
    assert image3.camera_view_setting == CameraViewSettings(None, None, None)
    assert image3.file_extension == "png"

    image4 = scene.images[3]
    assert image4.image_dir == "/root/image_4"
    assert image4.calib_dir is None
    assert image4.camera_view_setting is None
    assert image4.file_extension == "jpg"

    label1 = scene.labels[0]
    assert label1.label_dir == "/root/label_2"
    assert label1.image_dir == "/root/image_2"
    assert label1.calib_dir == "/root/calib"
    assert label1.file_extension == "png"

    label2 = scene.labels[1]
    assert label2.label_dir == "/root/label_4"
    assert label2.image_dir == "/root/image_4"
    assert label2.calib_dir == "/root/calib"
    assert label2.file_extension == "jpg"
