#!/bin/bash
# EC2 배포 스크립트 (app 폴더 기준)
# 이 스크립트는 EC2 서버의 /home/ubuntu/rag-app에서 실행됩니다.

set -e

echo "🚀 배포 시작..."

# 배포 디렉토리로 이동
cd /home/ubuntu/rag-app || {
  echo "❌ 배포 디렉토리를 찾을 수 없습니다: /home/ubuntu/rag-app"
  exit 1
}

# Python 가상환경 설정
echo "🔧 Python 가상환경 설정..."
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "📦 Python 가상환경 생성 중..."
  python3 -m venv venv
  source venv/bin/activate
fi

# 의존성 설치
echo "📦 의존성 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 서비스 재시작
echo "🔄 서비스 재시작 중..."
if systemctl is-active --quiet fastapi-rag; then
  sudo systemctl restart fastapi-rag
  echo "✅ FastAPI 서비스 재시작 완료"
else
  echo "⚠️ fastapi-rag 서비스가 없습니다."
  echo "💡 systemd 서비스를 설정하거나 수동으로 시작하세요."
fi

echo "✅ 배포 완료!"

# 헬스체크
echo "🏥 헬스체크 중..."
sleep 5

# 백엔드 헬스체크
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ 백엔드 헬스체크 성공"
else
  echo "⚠️ 백엔드 헬스체크 실패"
fi
