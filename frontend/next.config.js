const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 환경 변수는 NEXT_PUBLIC_ 접두사가 있으면 자동으로 클라이언트에 노출됨
  // next.config.js의 env 섹션은 선택사항

  webpack: (config, { isServer }) => {
    // tsconfig.json의 paths 설정과 일치하도록 webpack alias 설정
    // __dirname은 next.config.js가 있는 디렉토리(frontend)를 가리킴
    const rootPath = path.resolve(__dirname)

    // 기존 alias 유지하면서 @ 별칭 추가
    if (!config.resolve.alias) {
      config.resolve.alias = {}
    }

    config.resolve.alias['@'] = rootPath

    // 모듈 해석 개선
    if (!config.resolve.modules) {
      config.resolve.modules = []
    }

    // node_modules 경로 명시
    const nodeModulesPath = path.resolve(rootPath, 'node_modules')
    if (!config.resolve.modules.includes(nodeModulesPath)) {
      config.resolve.modules.unshift(nodeModulesPath)
    }

    return config
  },
}

module.exports = nextConfig
