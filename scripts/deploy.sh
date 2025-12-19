#!/bin/bash
# EC2 배포 스크립트
# 이 스크립트는 EC2 서버에서 직접 실행하거나 GitHub Actions에서 호출됩니다.

set -e

echo "🚀 배포 시작..."

# 프로젝트 디렉토리로 이동
cd ~/my_project/RAG || {
  echo "❌ 프로젝트 디렉토리를 찾을 수 없습니다."
  exit 1
}

# Git Pull
echo "📥 최신 코드 가져오기..."
git fetch origin
git reset --hard origin/main
git clean -fd

# 백엔드 배포
echo "🔧 백엔드 배포 중..."
if [ -d "venv" ]; then
  source venv/bin/activate
else
  python3 -m venv venv
  source venv/bin/activate
fi

# 백엔드 의존성 설치
pip install --upgrade pip
pip install -r app/requirements.txt

# 백엔드 서비스 재시작
if systemctl is-active --quiet fastapi-rag; then
  echo "🔄 백엔드 서비스 재시작 중..."
  sudo systemctl restart fastapi-rag
else
  echo "⚠️ fastapi-rag 서비스가 없습니다. 수동으로 시작하세요."
fi

# 프론트엔드 배포
echo "🎨 프론트엔드 배포 중..."
cd frontend

# Node.js 버전 확인
if ! command -v node &> /dev/null; then
  echo "❌ Node.js가 설치되지 않았습니다."
  exit 1
fi

# 의존성 설치
npm ci

# 빌드
npm run build

# 프론트엔드 서비스 재시작
if systemctl is-active --quiet nextjs-frontend; then
  echo "🔄 프론트엔드 서비스 재시작 중..."
  sudo systemctl restart nextjs-frontend
else
  echo "⚠️ nextjs-frontend 서비스가 없습니다. 수동으로 시작하세요."
fi

cd ..

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

# 프론트엔드 헬스체크
if curl -f http://localhost:3000 > /dev/null 2>&1; then
  echo "✅ 프론트엔드 헬스체크 성공"
else
  echo "⚠️ 프론트엔드 헬스체크 실패"
fi
