# 배포 스크립트

이 디렉토리에는 EC2 배포에 사용되는 스크립트가 포함되어 있습니다.

## 파일 설명

### `setup-ec2.sh`
EC2 서버 초기 설정 스크립트 (최초 1회만 실행)
- 시스템 패키지 설치
- Python, Node.js 설치
- Git 저장소 클론
- systemd 서비스 설정
- 서비스 시작

**사용법:**
```bash
chmod +x scripts/setup-ec2.sh
bash scripts/setup-ec2.sh
```

### `deploy.sh`
일반 배포 스크립트
- Git Pull
- 의존성 설치
- 서비스 재시작
- 헬스체크

**사용법:**
```bash
chmod +x scripts/deploy.sh
bash scripts/deploy.sh
```

## 주의사항

- 스크립트는 EC2 서버에서 실행해야 합니다
- `setup-ec2.sh`는 최초 1회만 실행하면 됩니다
- `deploy.sh`는 코드 업데이트 시마다 실행합니다
- GitHub Actions에서 자동으로 `deploy.sh`를 실행합니다
