# Vercel 배포 가이드

## 환경 변수 설정

Vercel 배포 시 다음 환경 변수를 설정하세요:

### 필수 환경 변수

```
NEXT_PUBLIC_API_URL=http://13.209.50.84:8000
```

### ⚠️ 포트 번호 필수

**포트 번호(`:8000`)를 반드시 포함해야 합니다!**

- ✅ 올바른 예: `http://13.209.50.84:8000`
- ❌ 잘못된 예: `http://13.209.50.84` (포트 80으로 연결 시도 → 실패)

**이유:**
- HTTP 기본 포트는 80, HTTPS 기본 포트는 443
- 백엔드는 포트 8000에서 실행 중
- 기본 포트가 아니므로 명시적으로 포트 번호를 지정해야 함

### 설명

- **NEXT_PUBLIC_API_URL**: 백엔드 API 서버 주소
  - EC2 인스턴스의 Public IP: `13.209.50.84`
  - 포트: `8000`
  - 전체 URL: `http://13.209.50.84:8000`

### 주의사항

1. **`NEXT_PUBLIC_` 접두사**: Next.js에서 클라이언트 사이드에서 접근 가능한 환경 변수는 `NEXT_PUBLIC_` 접두사가 필요합니다.

2. **OpenAI API 키는 필요 없음**:
   - OpenAI API 키는 **백엔드(EC2)의 `.env` 파일**에만 설정하면 됩니다.
   - 프론트엔드(Vercel)에서는 필요하지 않습니다.

3. **CORS 설정**:
   - 백엔드에서 이미 CORS가 활성화되어 있어 Vercel에서 호출 가능합니다.

## Vercel 배포 단계

### 1. 환경 변수 설정

Vercel 대시보드에서:
1. 프로젝트 선택
2. Settings → Environment Variables
3. 다음 변수 추가:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `http://13.209.50.84:8000`
   - **Environment**: Production, Preview, Development 모두 선택

### 2. 배포

```bash
# Vercel CLI 사용 시
vercel --prod

# 또는 GitHub 연동 시 자동 배포
git push origin main
```

## 환경별 설정

### Production (프로덕션)
```
NEXT_PUBLIC_API_URL=http://13.209.50.84:8000
```

### Preview (프리뷰)
```
NEXT_PUBLIC_API_URL=http://13.209.50.84:8000
```

### Development (개발)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 포트 번호 없이 사용하는 방법 (선택사항)

포트 번호를 생략하려면 Nginx 리버스 프록시를 설정해야 합니다:

### Nginx 설정 예시

```nginx
server {
    listen 80;
    server_name 13.209.50.84;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

이렇게 설정하면:
- `http://13.209.50.84` (포트 번호 없음) → 포트 80 → Nginx → 포트 8000
- Vercel 환경 변수: `NEXT_PUBLIC_API_URL=http://13.209.50.84`

하지만 현재는 **포트 번호를 포함하는 것이 가장 간단**합니다.

## 문제 해결

### CORS 오류
백엔드에서 CORS가 활성화되어 있는지 확인:
- `app/main.py`에서 `CORSMiddleware` 설정 확인
- `allow_origins=["*"]` 또는 Vercel 도메인 추가

### API 연결 실패
1. EC2 인스턴스가 실행 중인지 확인
2. Security Group에서 포트 8000이 열려있는지 확인
3. 백엔드 헬스체크: `http://13.209.50.84:8000/health`
4. **포트 번호가 포함되어 있는지 확인**: `:8000`이 URL에 있는지 확인

## 비용

- **Vercel**: 프리티어 사용 가능 (제한 있음)
- **EC2**: 인스턴스 실행 비용 (계속 발생)
- **OpenAI API**: 사용량 기반 (백엔드에서 처리)
