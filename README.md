# Resolution Calculator (해상도 계산기)

Python과 PySide6로 제작된 간단하면서도 강력한 GUI 애플리케이션입니다. 이미지/비디오 해상도, 종횡비, 총 픽셀 수를 계산하며, CG 아티스트, 비디오 편집자 등 다양한 화면이나 이미지 크기를 다루는 분들을 위해 설계되었습니다.

![image](https://github.com/user-attachments/assets/b571f7e8-7220-44eb-b74b-50d9d5d00292)

## 주요 기능

*   **해상도 입력:**
    *   정밀한 정수 스핀 박스를 사용하여 **너비(Width)** 와 **높이(Height)** 를 독립적으로 설정합니다.
    *   연결된 슬라이더를 사용하여 소수점 값(최대 두 자리)으로 미세 조정합니다.
    *   스핀 박스 옆에 소수점 부분을 시각적으로 표시합니다.
    *   **범위 확장(Extend Range)** 버튼을 통해 입력 범위를 조절할 수 있습니다 (기본: 최대 4096px, 확장: 최대 16384px).
*   **종횡비 계산:**
    *   현재 너비와 높이를 기준으로 **종횡비(Aspect Ratio)** 를 자동으로 계산하고 표시합니다.
    *   **비율 잠금(Lock Ratio):** 현재 종횡비를 유지하면서 너비 또는 높이를 조정합니다. 슬라이더를 드래그하는 동안 다른 치수가 실시간으로 업데이트됩니다.
    *   **비율 설정(Set Ratio):** 원하는 종횡비(예: `16:9`, `4:3`, `2.39:1`)를 수동으로 입력하고, 현재 너비 또는 높이를 기준으로 적용합니다.
*   **배율 조정:**
    *   주어진 배율(예: `1.5`, `2`, `0.5`)로 현재 해상도를 쉽게 **조정(Scale)** 합니다. 배율을 입력하고 Enter 키를 누릅니다.
*   **프리셋:**
    *   포괄적인 **프리셋(Presets)** 목록에서 일반적인 해상도와 종횡비를 빠르게 불러옵니다:
        *   표준 비디오/디스플레이 (SD, HD, FHD, QHD, 4K UHD)
        *   영화 표준 (DCI 2K/4K, Academy, Scope, IMAX)
        *   모바일 (세로 비율: 9:16, 9:19.5, 9:20, 9:21 등)
        *   태블릿 비율 (iPad, Android Tab 16:10, Surface 3:2)
        *   사진/일반 비율 (1:1, 3:2, 4:3, 5:4, 7:5)
    *   편의를 위해 프리셋 선택 후 목록이 기본값으로 재설정됩니다.
*   **총 픽셀 수:**
    *   **총 픽셀 수(Total Pixel Count)** (너비 x 높이)를 실시간으로 즉시 확인합니다.
*   **비율 및 크기 시각적 미리보기:**
    *   하단의 전용 미리보기 영역은 현재 해상도를 시각적으로 보여줍니다:
        *   **파란색 사각형:** 현재 너비/높이의 모양과 상대적인 크기를 나타냅니다.
        *   **녹색 점선 외곽선:** 크기 비교를 위해 표준 1920x1080 (FHD) 해상도를 나타냅니다.
        *   **회색 배경:** 일반적인 16:9 종횡비 영역을 나타냅니다.
    *   현재 해상도의 모양과 *크기*가 FHD 표준과 어떻게 다른지 직관적으로 이해할 수 있습니다.

## 설치 및 실행

**방법 1: 실행 파일 바로 다운로드 (Windows)**

1.  아래 링크에서 `resolution-cal.exe` 파일을 다운로드합니다.
    *   [**v1.0.0 다운로드 링크**](http://github.com/CharlieYang0040/resolution-cal/releases/download/v1.0.0/resolution-cal.exe)
2.  다운로드한 `resolution-cal.exe` 파일을 실행합니다.

**방법 2: 소스 코드 다운로드 및 자동 설정 (Windows)**

1.  **Git 저장소 복제(Clone) 또는 ZIP 다운로드:**
    *   Git 사용 시:
      ```bash
      git clone https://github.com/CharlieYang0040/resolution-cal.git
      cd resolution-cal
      ```
    *   ZIP 다운로드 시: GitHub 페이지에서 'Code' -> 'Download ZIP'을 클릭하고 압축을 해제합니다.
2.  **자동 실행 스크립트 실행:**
    *   프로젝트 폴더 내의 `run_calculator.bat` 파일을 더블 클릭하여 실행합니다.
    *   스크립트가 자동으로 Python 가상 환경(`resolution-cal-venv`)을 설정하고, 필요한 라이브러리(PySide6)를 설치한 후, 애플리케이션을 실행합니다.
    *   *(참고: 최초 실행 시 가상 환경 생성 및 라이브러리 설치 시간이 소요될 수 있습니다. Python이 설치되어 있어야 합니다.)*

## 실행 파일 빌드 (선택 사항)

PyInstaller가 `main.spec` 파일을 통해 설정되어 독립 실행형 파일을 빌드할 수 있습니다.

1.  PyInstaller가 설치되어 있는지 확인합니다 (`pip install pyinstaller`).
2.  spec 파일을 사용하여 PyInstaller를 실행합니다:
    ```bash
    pyinstaller main.spec
    ```
3.  실행 파일은 `dist/main` 폴더에서 찾을 수 있습니다.

    *참고: 아이콘 리소스 관련 빌드 오류(`BeginUpdateResourceW`, `ERROR_FILE_INVALID`) 발생 시, `main.spec` 파일에서 UPX 압축을 비활성화(`upx=False`)하거나 빌드 중 백신 프로그램을 잠시 비활성화해 보세요.*

## 주요 의존성

*   PySide6
*   Python 3.x

## 라이선스

*(선택 사항: 여기에 라이선스 정보를 추가하세요. 예: MIT 라이선스)* 
