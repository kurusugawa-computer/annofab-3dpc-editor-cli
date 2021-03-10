# KITTI形式（`KITTI 3D object detetection`）

## 概要
`project upload_kitti_data` コマンドで入力とするのは、3D物体検出で広く使われている KITTI形式（`KITTI 3D object detection`）の走行データになります。`KITTI 3D object detection` についての詳細は http://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d を参照してください。

## ディレクトリ構成


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
└── scene1/
    ├── velodyne/
    ├── image_2/
    ├── calib/
    ├── label_2/
```

シーンごとに以下のディレクトリが含まれています。以下のディレクトリ名は固定です。
* `velodyne`: 点群データ。(required)
* `image_2`: カメラ画像。(required)
* `calib`: キャリブレーション情報。(required)
* `label_2`: アノテーション情報。(optional)


## 各ディレクトリの詳細

### velodyne
binファイルには以下の情報が含まれています。
* x
* y
* z
* intensity

2021/03時点の3dpc-editorでは、intensityは参照していません。

binファイルの読み方は、以下を参照してください。

- https://github.com/yanii/kitti-pcl/blob/3b4ebfd49912702781b7c5b1cf88a00a8974d944/KITTI_README.TXT#L80:L87


### calib
キャリブレーションファイルのサンプルを以下に記載します。

```
P2: 1823.300048828125 0.0 960.0 0.0 0.0 1823.300048828125 227.0 0.0 0.0 0.0 1.0 0.0
R0_rect: 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0
Tr_velo_to_cam: -0.012217022641880869 0.9999253693940201 8.760178273212682e-09 -0.08186135136354311 0.008725876260145359 0.0001066209448708523 -0.9999619231328094 0.6023044315665451 -0.9998872953694633 -0.0122165573794921 -0.008726527633209977 -5.303541807824172
```

annofab-3dpc-editor-cliでは以下の項目を読み込みます。

* `P2`
* `R0_rect`
* `Tr_velo_to_cam`

各項目の詳細は以下を参照してください。

- https://medium.com/test-ttile/kitti-3d-object-detection-dataset-d78a762b5a4
- https://github.com/yanii/kitti-pcl/blob/3b4ebfd49912702781b7c5b1cf88a00a8974d944/KITTI_README.TXT#L142


### label_2

ラベルファイルのサンプルを以下に記載します。

```
Car 0.00 0 -1.59 583.21 175.79 697.83 284.07 1.56 1.65 3.69 0.42 1.63 12.33 -1.56
Car 0.00 0 -1.22 813.11 171.92 1060.81 315.73 1.49 1.63 4.16 4.43 1.49 9.52 -0.80
```

annofab-3dpc-editor-cliでは以下の項目を読み込みます。


* 0番目: 物体の種類。アノテーション仕様の`label_id`に対応します。
* 8番目: 3D-Height
* 9番目: 3D-Width
* 10番目: 3D-Length
* 11番目: 物体のX座標
* 12番目: 物体のY座標
* 13番目: 物体のZ座標
* 14番目: カメラ座標系でのY軸回転の向き


各項目の詳細は以下を参照してください。

- https://github.com/NVIDIA/DIGITS/issues/866
- http://hirotaka-hachiya.hatenablog.com/entry/2018/02/10/163432
