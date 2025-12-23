const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 환경 변수는 NEXT_PUBLIC_ 접두사가 있으면 자동으로 클라이언트에 노출됨
  // next.config.js의 env 섹션은 선택사항

  webpack: (config) => {
    // tsconfig.json의 paths 설정과 일치하도록 webpack alias 설정
    // __dirname은 next.config.js가 있는 디렉토리(frontend)를 가리킴
    const rootPath = path.resolve(__dirname)

    // 기존 alias를 유지하면서 @ 별칭 추가
    // Vercel 빌드 환경에서도 작동하도록 절대 경로 사용
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': rootPath,
    }

    // 확장자 해석 순서 명시
    config.resolve.extensions = [
      '.tsx',
      '.ts',
      '.jsx',
      '.js',
      '.json',
      ...(config.resolve.extensions || []),
    ]

    return config
  },
}

module.exports = nextConfig
