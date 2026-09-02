# 모바일 지연시간 벤치마크 (Mobile Benchmarks)

## 1. 실기기 벤치마크 결과

| 디바이스 | AP 프로세서 | 모델 | RTF (Real-Time Factor) | 5초 문장 합성 소요시간 | 메모리 점유율 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Galaxy S25 (SM-S931N)** | Snapdragon 8 Elite | VITS ONNX | **0.035x** | **0.18초** | ~68MB |
| **Galaxy A35 (SM-A356N)** | Exynos 1380 | VITS ONNX | **0.118x** | **0.59초** | ~72MB |
| **Galaxy S20 (SM-G981N)** | Snapdragon 865 | VITS ONNX | **0.142x** | **0.71초** | ~75MB |

> **RTF 공식**: $\text{RTF} = \frac{\text{합성에 소요된 연산 시간 (초)}}{\text{생성된 오디오 길이 (초)}}$  
> RTF가 1.0 미만이면 실시간 발화 속도보다 빠르게 합성됨을 의미합니다.
