@echo off
chcp 65001 > nul
echo.
echo ====================================
echo  Resolution Calculator 실행 스크립트
echo ====================================
echo.

@REM Python 설치 확인
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo Python 공식 웹사이트^(https://www.python.org/downloads/^)에서 설치 후 다시 시도해주세요.
    pause
    exit /b 1
)
echo [확인] Python 설치 확인 완료.
echo.

@REM 가상환경 디렉토리 설정 (스크립트 위치 기준)
set "VENV_NAME=resolution-cal-venv"
set "VIRTUAL_ENV=%~dp0%VENV_NAME%"

@REM 가상환경 폴더 존재 확인 및 생성
if not exist "%VIRTUAL_ENV%\Scripts\activate" (
    echo [정보] 가상환경^(%VENV_NAME%^)을 생성합니다...
    python -m venv "%VENV_NAME%"
    if %ERRORLEVEL% neq 0 (
        echo [오류] 가상환경 생성에 실패했습니다. Python -m venv 명령어를 확인해주세요.
        pause
        exit /b 1
    )
    echo [성공] 가상환경이 생성되었습니다: %VIRTUAL_ENV%
    echo.
) else (
    echo [정보] 기존 가상환경^(%VENV_NAME%^)을 사용합니다.
    echo.
)

@REM 가상환경 경로를 PATH에 추가 (암묵적 활성화)
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
echo [정보] 가상환경 경로를 PATH에 추가했습니다.
rem set "PYTHONPATH=%VIRTUAL_ENV%\Lib\site-packages;%PYTHONPATH%"

@REM 가상환경 내 Python 인터프리터 확인
if exist "%VIRTUAL_ENV%\\Scripts\\python.exe" (
    echo [정보] 사용될 Python 인터프리터: "%VIRTUAL_ENV%\\Scripts\\python.exe"
    "%VIRTUAL_ENV%\\Scripts\\python.exe" -c "import sys; print('[정보] Python 버전: ' + str(sys.version))"
    echo.
) else (
    echo [오류] 가상환경 내 Python 인터프리터^(%VIRTUAL_ENV%\\Scripts\\python.exe^)를 찾을 수 없습니다.
    echo 가상환경이 올바르게 생성되었는지 확인해주세요.
    pause
    exit /b 1
)

@REM requirements.txt 파일 확인
if not exist "%~dp0requirements.txt" (
    echo [오류] requirements.txt 파일을 찾을 수 없습니다. ^(%~dp0requirements.txt^)
    pause
    exit /b 1
)

@REM 의존성 설치 (pip 사용)
echo [정보] 필요한 라이브러리를 설치합니다 (requirements.txt)...
"%VIRTUAL_ENV%\\Scripts\\pip.exe" install -r "%~dp0requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo [오류] 라이브러리 설치 중 오류가 발생했습니다. pip install 명령어를 확인해주세요.
    pause
    exit /b 1
)
echo [성공] 라이브러리 설치 완료.
echo.

@REM main.py 파일 확인 및 실행
if exist "%~dp0main.py" (
    echo [정보] Resolution Calculator를 실행합니다...
    echo.
    "%VIRTUAL_ENV%\\Scripts\\python.exe" "%~dp0main.py"
) else (
    echo [오류] main.py 파일을 찾을 수 없습니다. ^(%~dp0main.py^)
    pause
    exit /b 1
)

echo.
echo [정보] Resolution Calculator 실행 완료.
pause 