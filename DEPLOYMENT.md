# 배포 가이드

이 문서는 EC2에 FastAPI 백엔드와 Next.js 프론트엔드를 배포하는 방법을 설명합니다.

## 📋 사전 요구사항

### 1. EC2 인스턴스
- Ubuntu 24.04 LTS
- 최소 8GB RAM (모델 로딩용)
- 최소 20GB 디스크 공간
- 보안 그룹 설정:
  - 포트 22 (SSH)
  - 포트 8000 (FastAPI 백엔드)
  - 포트 3000 (Next.js 프론트엔드)

### 2. GitHub 설정
- GitHub 저장소
- GitHub Secrets 설정 (아래 참조)

## 🔐 GitHub Secrets 설정

GitHub 저장소의 Settings → Secrets and variables → Actions에서 다음 Secrets를 추가하세요:

| Secret 이름 | 설명 | 예시 |
|------------|------|------|
| `EC2_HOST` | EC2 퍼블릭 DNS | `ec2-13-209-50-84.ap-northeast-2.compute.amazonaws.com` |
| `EC2_USER` | EC2 사용자명 | `ubuntu` |
| `EC2_SSH_KEY` | SSH 개인 키 내용 | `kroaddy.pem` 파일의 전체 내용 |

### SSH 키 설정 방법

1. 로컬에서 SSH 키 확인:
   ```bash
   cat kroaddy.pem
   ```

2. 전체 내용을 복사하여 GitHub Secret `EC2_SSH_KEY`에 붙여넣기

3. EC2에서 공개 키 등록 (선택사항):
   ```bash
   # 로컬에서
   ssh-keygen -y -f kroaddy.pem > kroaddy.pub

   # EC2에서
   cat kroaddy.pub >> ~/.ssh/authorized_keys
   ```

## 🚀 배포 프로세스

### 방법 1: 자동 배포 (GitHub Actions)

**중요**: `app/` 폴더의 파일이 변경될 때만 자동 배포가 실행됩니다.

1. **코드 푸시**
   ```bash
   git add app/
   git commit -m "Update backend"
   git push origin main
   ```

2. **GitHub Actions 자동 실행**
   - GitHub 저장소의 Actions 탭에서 진행 상황 확인
   - `app/**` 경로 변경 감지 시 자동 배포 실행
   - 수동 배포: Actions → "Deploy app to EC2" → "Run workflow"

### 방법 2: 수동 배포

1. **EC2에 SSH 접속**
   ```bash
   ssh -i kroaddy.pem ubuntu@ec2-13-209-50-84.ap-northeast-2.compute.amazonaws.com
   ```

2. **배포 스크립트 실행**
   ```bash
   cd ~/rag-app
   bash scripts/deploy.sh
   ```

## 🔧 EC2 초기 설정 (최초 1회)

EC2 서버에서 다음 스크립트를 실행하여 초기 환경을 설정합니다:

```bash
# EC2에 SSH 접속 후
cd ~
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/scripts/setup-ec2.sh
chmod +x setup-ec2.sh
bash setup-ec2.sh
```

또는 로컬에서 스크립트를 업로드:

```bash
# 로컬에서
scp -i kroaddy.pem scripts/setup-ec2.sh ubuntu@ec2-13-209-50-84.ap-northeast-2.compute.amazonaws.com:~/

# EC2에서
chmod +x setup-ec2.sh
bash setup-ec2.sh
```

**참고**: 초기 설정 후 배포 디렉토리는 `/home/ubuntu/rag-app`입니다.

## 📝 환경 변수 설정

EC2 서버에서 `.env` 파일을 생성/수정:

```bash
cd ~/rag-app
nano .env
```

필수 환경 변수:
```bash
OPENAI_API_KEY=your-openai-api-key-here
DATABASE_URL=postgresql://neondb_owner:npg_2CUgeTP5KBuO@ep-restless-cell-a1n05rxq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
LLM_PROVIDER=midm
DEBUG=false
```

## 🤖 모델 파일 업로드

Midm 모델 파일을 EC2에 업로드:

```bash
# 로컬에서
scp -i kroaddy.pem -r app/model/midm ubuntu@ec2-13-209-50-84.ap-northeast-2.compute.amazonaws.com:~/rag-app/model/
```

또는 S3를 사용하여 업로드 (대용량 파일의 경우)

## 🛠️ 서비스 관리

### 서비스 상태 확인
```bash
sudo systemctl status fastapi-rag
```

### 서비스 시작/중지/재시작
```bash
# 백엔드
sudo systemctl start fastapi-rag
sudo systemctl stop fastapi-rag
sudo systemctl restart fastapi-rag
```

### 로그 확인
```bash
# 백엔드 로그
sudo journalctl -u fastapi-rag -f

# 최근 로그만 보기
sudo journalctl -u fastapi-rag -n 100
```

## 🌐 접근 확인

배포 후 다음 URL로 접근 가능:

- **백엔드 API**: `http://EC2_PUBLIC_IP:8000`
- **API 문서**: `http://EC2_PUBLIC_IP:8000/docs`
- **헬스체크**: `http://EC2_PUBLIC_IP:8000/health`

## 🔍 문제 해결

### 배포 실패 시

1. **GitHub Actions 로그 확인**
   - GitHub 저장소 → Actions 탭 → 실패한 워크플로우 클릭

2. **EC2 서버 로그 확인**
   ```bash
   sudo journalctl -u fastapi-rag -n 50
   ```

3. **수동 배포 시도**
   ```bash
   cd ~/rag-app
   bash scripts/deploy.sh
   ```

### 서비스가 시작되지 않을 때

1. **의존성 확인**
   ```bash
   cd ~/rag-app
   source venv/bin/activate
   pip list
   ```

2. **포트 충돌 확인**
   ```bash
   sudo netstat -tulpn | grep 8000
   ```

3. **환경 변수 확인**
   ```bash
   cd ~/rag-app
   cat .env
   ```

4. **수동 실행 테스트**
   ```bash
   cd ~/rag-app
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 🔄 롤백 방법

이전 버전으로 롤백:

```bash
cd ~/rag-app
# rsync로 이전 버전 복원하거나
# GitHub Actions에서 이전 커밋으로 재배포
```

## 📊 모니터링

### 리소스 사용량 확인
```bash
# CPU, 메모리 사용량
htop

# 디스크 사용량
df -h

# 네트워크 사용량
iftop
```

### 헬스체크
```bash
# 백엔드
curl http://localhost:8000/health
```

## 🔒 보안 권장사항

1. **SSH 키 보안**
   - SSH 키는 절대 Git에 커밋하지 않음
   - GitHub Secrets에만 저장

2. **방화벽 설정**
   - EC2 보안 그룹에서 필요한 포트만 오픈
   - SSH는 특정 IP만 허용 (선택사항)

3. **환경 변수 보안**
   - `.env` 파일은 Git에 포함하지 않음
   - 민감한 정보는 GitHub Secrets 사용

4. **HTTPS 설정** (선택사항)
   - Nginx 리버스 프록시 설정
   - Let's Encrypt SSL 인증서 적용

## 📚 추가 리소스

- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Next.js 프로덕션 배포](https://nextjs.org/docs/deployment)
- [systemd 서비스 관리](https://www.digitalocean.com/community/tutorials/how-to-use-systemctl-to-manage-systemd-services-and-units)
