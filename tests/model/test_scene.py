import re

from anno3d.model.scene import XYZ, Scene


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
    }
  ],
  // これ以外の項目はoptionとする．有ろうが無かろうが，3DPCE側は気にしない．
  "dummy": "value"
}"""
    comment_removed = "\n".join([re.sub("//.*", "", line) for line in json.split("\n")])
    scene = Scene.decode(comment_removed)
    assert len(scene.id_list) == 2
    assert scene.id_list[0] == "006497"
    assert scene.id_list[1] == "012187"
    assert scene.velodyne.velodyne_dir == "velodyne"
    assert len(scene.images) == 2
    assert len(scene.labels) == 1

    image1 = scene.images[0]
    assert image1.image_dir == "image_rf"
    assert image1.calib_dir is None
    assert image1.camera_view_setting.fov == 1.57
    assert image1.camera_view_setting.direction == 0.92
    assert image1.camera_view_setting.position == XYZ(-2.0, -1.0, 0.8)

    image2 = scene.images[1]
    assert image2.image_dir == "image_2"
    assert image2.calib_dir == "calib"
    assert image2.camera_view_setting is None

    label = scene.labels[0]
    assert label.label_dir == "label_2"
    assert label.image_dir == "image_2"
    assert label.calib_dir == "calib"
