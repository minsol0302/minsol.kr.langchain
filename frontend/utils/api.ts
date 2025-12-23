/**
 * API 클라이언트
 * 백엔드 API와 통신하는 함수들
 */

// 환경 변수 접근 (Next.js는 NEXT_PUBLIC_ 접두사가 있으면 자동으로 클라이언트에 노출)
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string | Date  // 직렬화를 위해 string도 허용
  sources?: DocumentSource[]
}

export interface DocumentSource {
  content: string
  metadata: Record<string, any>
}

export interface RAGResponse {
  question: string
  answer: string
  sources?: DocumentSource[]
}

export const chatAPI = {
  /**
   * RAG 챗봇에 메시지 전송
   * @param message 사용자 메시지
   * @param k 검색할 문서 개수 (기본값: 3)
   */
  async sendMessage(message: string, k: number = 3): Promise<RAGResponse> {
    if (!API_URL) {
      throw new Error('API URL이 설정되지 않았습니다. NEXT_PUBLIC_API_URL 환경 변수를 확인하세요.')
    }

    try {
      const response = await fetch(`${API_URL}/rag/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message,
          k: k,
        }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error: any) {
      // 네트워크 오류 처리
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`서버에 연결할 수 없습니다. API URL: ${API_URL}`)
      }
      throw error
    }
  },
}
