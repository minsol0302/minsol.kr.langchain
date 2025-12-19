# HTTPS 설정 가이드

## ⚠️ 문제: Mixed Content 오류

**오류 메시지:**
```
Mixed Content: The page at 'https://minsol-kr-langchain.vercel.app/'
was loaded over HTTPS, but requested an insecure resource
'http://13.209.50.84:8000/rag/query'.
This request has been blocked.
```

**원인:**
- Vercel은 HTTPS로 서비스됨
- EC2 백엔드는 HTTP로 실행 중
- 브라우저가 HTTPS 페이지에서 HTTP 리소스를 차단 (보안 정책)

## 해결 방법

### 방법 1: Nginx + Let's Encrypt (권장)

EC2에 Nginx를 설치하고 Let's Encrypt로 SSL 인증서를 발급받습니다.

#### 1. 도메인 이름 필요
- 도메인이 EC2 IP를 가리켜야 합니다
- 예: `api.yourdomain.com` → `13.209.50.84`

#### 2. SSL 설정 스크립트 실행

```bash
# EC2에 SSH 접속
ssh ubuntu@13.209.50.84

# 스크립트 다운로드 및 실행
cd ~
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/scripts/setup-nginx-ssl.sh
chmod +x setup-nginx-ssl.sh
sudo bash setup-nginx-ssl.sh
```

#### 3. Vercel 환경 변수 업데이트

```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 방법 2: 임시 해결책 (HTTP 프록시)

도메인이 없는 경우, Nginx를 HTTP 프록시로만 설정:

```bash
# EC2에서
sudo apt-get install -y nginx

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
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fastapi-rag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

**하지만 이것도 Mixed Content 문제를 해결하지 못합니다.**

### 방법 3: Vercel Rewrites (제한적)

Vercel의 `next.config.js`에서 rewrites를 사용할 수 있지만,
백엔드가 HTTPS가 아니면 여전히 문제가 발생합니다.

## 권장 해결책

**도메인을 구매하고 Nginx + Let's Encrypt로 HTTPS를 설정하세요.**

1. 도메인 구매 (예: Namecheap, GoDaddy)
2. 도메인 DNS에 A 레코드 추가: `api.yourdomain.com` → `13.209.50.84`
3. `setup-nginx-ssl.sh` 스크립트 실행
4. Vercel 환경 변수 업데이트

## 빠른 테스트 (개발용)

개발 환경에서만 테스트하려면:

1. 브라우저에서 Mixed Content 허용 (권장하지 않음)
2. 또는 로컬에서 HTTP로 테스트

## 비용

- Let's Encrypt: 무료
- 도메인: 연간 $10-15 (선택사항이지만 권장)
