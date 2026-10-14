# DF-ENGINE-IDENTITY-001 — 얼굴 일관성 평가기

후보 이미지가 MASTER 와 같은 얼굴인지, SOPHIE·F30 같은 보호 대상과 겹치지 않는지 점수를 낸다.
상업 이용 가능한 OpenCV zoo YuNet(MIT) + SFace(Apache-2.0) 만 쓴다. CPU 만 쓴다.

```
pip install opencv-python-headless==4.10.0.84 numpy
mkdir models && cd models
curl -LO https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -LO https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
cd ..
python -m df_identity --models models --master master_front.png --candidate cand_01.png \
  --protected SOPHIE_V1_1=sophie_master.png --out eval.json
```

모델 해시는 `models.json` 과 다르면 실행을 멈춘다.

판정: `PASS_CANDIDATE` / `REVIEW` / `FAIL_DRIFT` / `BLOCK_PROTECTED` / `ERROR`. 구간은 `Policy` 에 있고 아직 AI 생성 얼굴로 보정하지 않았다(`calibrated: false`). 점수는 보조이고 MASTER LOCK 은 사람이 한다.

시험: `DF_ID_MODELS=models DF_ID_SMOKE_DIR=smoke python -m unittest discover -s tests -t tests`.
`smoke/largest_selfie.jpg` 는 opencv_zoo `models/face_detection_yunet/example_outputs/largest_selfie.jpg` 이다. 실존 인물 사진이라 저장소에 넣지 않는다.

얼굴 특징 벡터는 결과에 남기지 않는다.
