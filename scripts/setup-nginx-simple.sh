#!/bin/bash
# Nginx 간단 프록시 설정 (HTTP만, SSL 없음)
# Mixed Content 문제는 해결하지 못하지만, 포트 80으로 접근 가능하게 함

set -e

echo "🔧 Nginx 프록시 설정 시작..."

# Nginx 설치
if ! command -v nginx &> /dev/null; then
  echo "📦 Nginx 설치 중..."
  sudo apt-get update
  sudo apt-get install -y nginx
fi

# Nginx 설정
echo "📝 Nginx 설정 파일 생성 중..."
sudo tee /etc/nginx/sites-available/fastapi-rag > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # CORS 헤더 추가
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # OPTIONS 요청 처리
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE';
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain';
            return 204;
        }
    }
}
EOF

# 설정 활성화
sudo ln -sf /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx 설정 테스트
echo "🔍 Nginx 설정 테스트 중..."
sudo nginx -t

# Nginx 재시작
echo "🔄 Nginx 재시작 중..."
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "✅ Nginx 프록시 설정 완료!"
echo ""
echo "⚠️ 주의: 이것은 HTTP 프록시입니다."
echo "⚠️ Mixed Content 문제를 해결하려면 HTTPS가 필요합니다."
echo "💡 도메인을 구매하고 setup-nginx-ssl.sh를 실행하세요."
