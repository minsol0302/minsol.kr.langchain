#!/bin/bash
# EC2 초기 설정 스크립트
# 이 스크립트는 EC2 서버에서 한 번만 실행하면 됩니다.

set -e

echo "🔧 EC2 초기 설정 시작..."

# 시스템 업데이트
echo "📦 시스템 패키지 업데이트..."
sudo apt update
sudo apt upgrade -y

# 필수 패키지 설치
echo "📦 필수 패키지 설치..."
sudo apt install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  nodejs \
  npm \
  git \
  curl \
  nginx \
  build-essential

# Node.js 버전 확인 및 업그레이드 (필요시)
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
  echo "📦 Node.js 업그레이드 중..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt install -y nodejs
fi

# 프로젝트 디렉토리 생성
echo "📁 프로젝트 디렉토리 생성..."
mkdir -p ~/my_project
cd ~/my_project

# Git 저장소 클론 (이미 있으면 스킵)
if [ ! -d "RAG" ]; then
  echo "📥 Git 저장소 클론..."
  git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git RAG
  cd RAG
else
  echo "ℹ️ 저장소가 이미 존재합니다."
  cd RAG
fi

# Python 가상환경 생성
echo "🐍 Python 가상환경 생성..."
python3.11 -m venv venv
source venv/bin/activate

# 백엔드 의존성 설치
echo "📦 백엔드 의존성 설치..."
pip install --upgrade pip
pip install -r app/requirements.txt

# 프론트엔드 의존성 설치
echo "📦 프론트엔드 의존성 설치..."
cd frontend
npm install
npm run build
cd ..

# .env 파일 생성 (템플릿)
if [ ! -f ".env" ]; then
  echo "📝 .env 파일 생성..."
  cat > .env << EOF
# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Neon PostgreSQL
DATABASE_URL=postgresql://neondb_owner:npg_2CUgeTP5KBuO@ep-restless-cell-a1n05rxq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# LLM Provider
LLM_PROVIDER=midm

# Debug
DEBUG=false
EOF
  echo "⚠️ .env 파일을 수정하여 실제 값을 입력하세요!"
fi

# systemd 서비스 파일 생성
echo "⚙️ systemd 서비스 설정..."

# 백엔드 서비스
sudo tee /etc/systemd/system/fastapi-rag.service > /dev/null << EOF
[Unit]
Description=FastAPI RAG Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/my_project/RAG
Environment="PATH=/home/ubuntu/my_project/RAG/venv/bin"
EnvironmentFile=/home/ubuntu/my_project/RAG/.env
ExecStart=/home/ubuntu/my_project/RAG/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 프론트엔드 서비스
sudo tee /etc/systemd/system/nextjs-frontend.service > /dev/null << EOF
[Unit]
Description=Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/my_project/RAG/frontend
Environment="PATH=/usr/local/bin:/usr/bin"
Environment="NEXT_PUBLIC_API_URL=http://localhost:8000"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화 및 시작
echo "🚀 서비스 시작..."
sudo systemctl daemon-reload
sudo systemctl enable fastapi-rag
sudo systemctl enable nextjs-frontend
sudo systemctl start fastapi-rag
sudo systemctl start nextjs-frontend

# 서비스 상태 확인
echo "📊 서비스 상태 확인..."
sudo systemctl status fastapi-rag --no-pager
sudo systemctl status nextjs-frontend --no-pager

echo "✅ EC2 초기 설정 완료!"
echo ""
echo "다음 단계:"
echo "1. .env 파일을 수정하여 실제 환경 변수를 설정하세요"
echo "2. app/model/midm 디렉토리에 모델 파일을 업로드하세요"
echo "3. 서비스 로그 확인: sudo journalctl -u fastapi-rag -f"
echo "4. 서비스 로그 확인: sudo journalctl -u nextjs-frontend -f"
