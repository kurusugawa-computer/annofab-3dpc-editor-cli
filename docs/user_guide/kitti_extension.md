
# 拡張KITTI形式

## 概要
[KITTI形式(KITTI 3D object detetection)](kitti_3d_object_detection.md) に以下の拡張性を持たせた、KCI独自のフォーマットです。以下の項目に該当する要件がある場合には本形式の走行データを入力としてください。それ以外の場合は、標準の[KITTI形式](kitti_3d_object_detection.md)をお使いいただくことを推奨します。

* あるシーンに紐づく複数のカメラ画像（例：側方カメラ）をアップロードできる
* `velodyne`, `image_2`などのディレクトリ名を変更できる
* アノテーション情報が格納されたラベルファイルに、Annofabの`annotation_id`を格納できる
* 3dpc-editorで表示されるカメラの向き及び視野角を設定できる

※実用上の観点から定めている形式であり，将来的に変更される可能性があります。

## ディレクトリ構成

`scene.meta`ファイルには、各データが格納されているディレクトリなどが記載されています。
`scene.meta`ファイルが存在しない場合、入力走行データは[KITTI形式](kitti_3d_object_detection.md)として扱われます。


```
.
└── scene0/
    ├── velodyne/
    │   ├── frame1.bin
    │   ├── frame2.bin
    │   ├── ...
    ├── image_2/
    │   ├── frame1.png
    │   ├── frame2.png
    │   ├── ...
    ├── calib/
    │   ├── frame1.txt
    │   ├── frame2.txt
    │   ├── ...
    ├── label_2/
    │   ├── frame1.txt
    │   ├── frame2.txt
    │   ├── ...
    ├── scene.meta
└── scene1/
    ├── velodyne/
    ├── image_2/
    ├── calib/
    ├── label_2/
    ├── scene.meta
└── scene2/
```


## scene.meta

### 基本的なパターン
以下の`scene.meta`は、KITTI形式と同じディレクトリ構成を表しています。

```json
{
  "id_list": [
    "frame1",
    "frame2"
  ],
  "serieses": [
    {
        "type": "kitti_velodyne",
        "velodyne_dir": "velodyne"  // 点群データが格納されているディレクトリの名前
    },
    {
        "type": "kitti_image",
        "image_dir": "image_2", // カメラ画像ファイルが格納されているディレクトリの名前
        "calib_dir": "calib", // image_2に紐づくキャリブレーション情報が格納されているディレクトリの名前。
        "file_extension": "png" // カメラ画像ファイルの拡張子
    },
    {
        "type": "kitti_label",
        "label_dir": "label_2", // ラベルファイルが格納されているディレクトリの名前
        "image_dir": "image_2", // label_2に紐づくカメラ画像ファイルが格納されているディレクトリの名前
        "calib_dir": "calib"    // label_2に紐づくキャリブレーション情報が格納されているディレクトリの名前
    }
  ],
}
```


```
scene0/
├── velodyne/
│   ├── frame1.bin
│   ├── frame2.bin
├── image_2/
│   ├── frame1.png
│   ├── frame2.png
├── calib/
│   ├── frame1.txt
│   ├── frame2.txt
├── label_2/
│   ├── frame1.txt
│   ├── frame2.txt
├── scene.meta
```

### カメラの向き及び視野角を設定する場合


```json
{
  "id_list": [
    "frame1",
    "frame2"
  ],
  "serieses": [
    {
        "type": "kitti_velodyne",
        "velodyne_dir": "velodyne"  // 点群データが格納されているディレクトリの名前
    },
    {
        "type": "kitti_image",
        "image_dir": "image_2", 
        "calib_dir": "calib",
        "camera_view_setting": {  // 3dpc-editorの視野角
            "fov": 1.57,    // field of view [radian]
            "direction": 0.92,  // Z軸の回転[radian]。Velodyne座標系のX軸方向が0.0
            "position": {   // Velodyne座標系に対するカメラ位置
                "x": -2.0,
                "y": -1.0,
                "z": 0.8
            },
        },
    },
  ],
}
```



### カメラが2種類ある場合


```json
{
  "id_list": [
    "frame1",
    "frame2"
  ],
  "serieses": [
    {
        "type": "kitti_velodyne",
        "velodyne_dir": "velodyne"
    },
    {
        "type": "kitti_image",
        "image_dir": "image_rear", 
        "calib_dir": "calib_rear" 
    },
    {
        "type": "kitti_image",
        "image_dir": "image_front",
        "calib_dir": "calib_front" 
    },
  ],
}
```

```
scene0/
├── velodyne/
│   ├── frame1.bin
│   ├── frame2.bin
├── image_front/
│   ├── frame1.png
│   ├── frame2.png
├── calib_front/
│   ├── frame1.txt
│   ├── frame2.txt
├── image_rear/
│   ├── frame1.png
│   ├── frame2.png
├── calib_rear/
│   ├── frame1.txt
│   ├── frame2.txt
├── scene.meta
```



## ラベルファイル
ラベルファイルの15番目の要素に、AnnoFabの`annotation_id`を格納できます。


