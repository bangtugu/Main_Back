## 환경 구성
```bash

#오라클 11g버전 설치 url
https://www.oracle.com/database/technologies/xe-prior-release-downloads.html
#Oracle Instant Client 설치 url
https://www.oracle.com/database/technologies/instant-client.html
#dbeaver 설치 url (선택)
https://dbeaver.io/download/

#가상환경 생성
conda create -n env_name python=3.10
#가상환경 실행
conda activate env_name

#3070ti, 본인 환경에 맞는 토치, 토치비전 등 우선설치. pip 먼저하면 의존 따라서 cpu버전이 임의로 깔릴 수 있음. 
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y

# pykospacing install
pip install git+https://github.com/haven-jeon/PyKoSpacing.git
# requirements.txt
pip install -r requirements.txt
```

## db 구성
```bash
# create_user_file.py 내부 db 접속 정보 입력
# Oracle Instant Client 다운로드 받은 경로 설정
lib_dir = 'PATH'
# ex ) C:\Users\PC1\Desktop\oracle\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28
# 오라클 테이블에 맞는 아이디, 비밀번호 입력
user = '아이디'
password = '비밀번호'

# db 테이블 구현
python create_user_file.py
```

```bash
# https://developer.hancom.com/hwpautomation
# hwp 보안모듈 관련 링크
```

## extractor, classificator fastapi backend실행
``` bash
# 포트 8002번 classificator 작동
cd classificator
python main.py
cd ..

# 포트 8001번 extractor 작동
cd extractor
python main.py
cd ..
```

