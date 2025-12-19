#!/bin/bash
# Nginx + Let's Encrypt SSL 설정 스크립트
# EC2에서 백엔드를 HTTPS로 제공하기 위한 설정

set -e

echo "🔒 Nginx + SSL 설정 시작..."

# Nginx 설치
echo "📦 Nginx 설치 중..."
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 도메인 이름 입력 (없으면 IP 주소 사용)
read -p "도메인 이름을 입력하세요 (없으면 Enter): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
  echo "⚠️ 도메인 이름이 없습니다. IP 주소로 설정합니다."
  DOMAIN_NAME=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
  echo "📌 IP 주소: $DOMAIN_NAME"
  echo "⚠️ IP 주소로는 SSL 인증서를 발급받을 수 없습니다."
  echo "💡 임시 해결책: Nginx를 HTTP로 설정하고 프록시만 구성합니다."

  # IP 주소인 경우 HTTP 프록시만 설정
  sudo tee /etc/nginx/sites-available/fastapi-rag > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS 헤더 추가
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type' always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

  sudo ln -sf /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
  sudo rm -f /etc/nginx/sites-enabled/default

  sudo nginx -t
  sudo systemctl restart nginx
  sudo systemctl enable nginx

  echo "✅ Nginx HTTP 프록시 설정 완료"
  echo "⚠️ HTTPS를 사용하려면 도메인 이름이 필요합니다."
  exit 0
fi

# 도메인 이름이 있는 경우 SSL 설정
echo "📝 도메인 이름: $DOMAIN_NAME"

# Nginx 기본 설정
sudo tee /etc/nginx/sites-available/fastapi-rag > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx 설정 테스트
sudo nginx -t

# Nginx 시작
sudo systemctl restart nginx
sudo systemctl enable nginx

# Let's Encrypt SSL 인증서 발급
echo "🔐 SSL 인증서 발급 중..."
sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME || {
  echo "⚠️ SSL 인증서 발급 실패"
  echo "💡 도메인이 EC2 IP를 가리키고 있는지 확인하세요."
  exit 1
}

# 자동 갱신 설정
sudo systemctl enable certbot.timer

echo "✅ Nginx + SSL 설정 완료!"
echo ""
echo "📌 백엔드 URL: https://$DOMAIN_NAME"
echo "💡 Vercel 환경 변수를 업데이트하세요:"
echo "   NEXT_PUBLIC_API_URL=https://$DOMAIN_NAME"
