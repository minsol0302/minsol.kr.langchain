const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 환경 변수는 NEXT_PUBLIC_ 접두사가 있으면 자동으로 클라이언트에 노출됨
  // next.config.js의 env 섹션은 선택사항

  webpack: (config) => {
    // tsconfig.json의 paths 설정과 일치하도록 webpack alias 설정
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
    }
    return config
  },
}

module.exports = nextConfig
