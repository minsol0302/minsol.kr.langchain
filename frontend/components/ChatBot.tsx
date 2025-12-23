'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Bot, User } from 'lucide-react'
import { chatAPI, Message, DocumentSource } from '../lib/api'

export default function ChatBot() {
  // 클라이언트에서만 초기 메시지 설정 (hydration 오류 방지)
  const [messages, setMessages] = useState<Message[]>([])
  const [isMounted, setIsMounted] = useState(false)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // 클라이언트 마운트 후 초기 메시지 설정
  useEffect(() => {
    setIsMounted(true)
    setMessages([
      {
        role: 'assistant',
        content: '안녕하세요! RAG 챗봇입니다. 무엇이 궁금하신가요?',
        timestamp: new Date().toISOString(),
      },
    ])
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    // 클라이언트에서만 실행
    if (typeof window !== 'undefined') {
      scrollToBottom()
    }
  }, [messages])

  // 컴포넌트 마운트 시 입력 필드에 자동 포커스
  useEffect(() => {
    // 클라이언트에서만 실행
    if (typeof window !== 'undefined') {
      inputRef.current?.focus()
    }
  }, [])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input.trim()
    setInput('')
    setIsLoading(true)

    try {
      const response = await chatAPI.sendMessage(currentInput, 3)

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer || '응답을 생성할 수 없습니다.',
        timestamp: new Date().toISOString(),
        sources: Array.isArray(response.sources)
          ? response.sources.map((doc: any) => ({
            content: doc.content || '',
            metadata: doc.metadata || {},
          }))
          : [],
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: error?.message?.includes('fetch')
          ? '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.'
          : '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      // 클라이언트에서만 포커스
      if (typeof window !== 'undefined') {
        setTimeout(() => {
          inputRef.current?.focus()
        }, 0)
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }


  // 클라이언트 마운트 전에는 빈 화면 (hydration 오류 방지)
  if (!isMounted) {
    return (
      <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg overflow-hidden">
      {/* 메시지 영역 */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4 chat-messages"
        style={{
          paddingBottom: '100px' // 입력 영역 공간 확보
        }}
      >
        {messages.map((message, index) => (
          <div
            key={`message-${index}-${message.timestamp}`}
            className={`flex items-start gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${message.role === 'user'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-800'
                }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>

              {/* 소스 문서 표시 */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300">
                  <p className="text-xs font-semibold mb-1">참조 문서:</p>
                  {message.sources.map((source, idx) => (
                    <div
                      key={`source-${idx}-${source.content?.substring(0, 20)}`}
                      className="text-xs bg-white bg-opacity-50 rounded p-2 mb-1"
                    >
                      <p className="line-clamp-2">{source.content || ''}</p>
                    </div>
                  ))}
                </div>
              )}

              {message.timestamp && isMounted && (
                <p className="text-xs mt-1 opacity-70" suppressHydrationWarning>
                  {new Date(message.timestamp).toLocaleTimeString('ko-KR', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                <User className="w-5 h-5 text-gray-600" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div
        className="border-t border-gray-200 p-4 bg-white chat-input-area shadow-lg flex-shrink-0"
      >
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            onKeyDown={handleKeyPress}
            placeholder="메시지를 입력하세요..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-text text-gray-900"
            disabled={isLoading}
            tabIndex={0}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            <span>전송</span>
          </button>
        </div>
      </div>
    </div>
  )
}

