import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { MessageCircle, Send, X } from "lucide-react"
import { ScrollArea } from './ui/scroll-area'

export function ChatBar() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{
    id: number;
    text: string;
    sender: string;
    relatedImages?: string[];
    sources?: Array<{
      metadata?: { title?: string; url?: string };
      content?: string;
    }>;
  }>>([
    { id: 1, text: "Hello! How can I help you today? ✨", sender: "assistant" },
  ])
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async () => {
    if (message.trim() && !isLoading) {
      setIsLoading(true)

      // Add user message
      const newMessage = {
        id: messages.length + 1,
        text: message,
        sender: "user"
      }

      const updatedMessages = [...messages, newMessage]
      setMessages(updatedMessages)

      const currentMessage = message
      setMessage('')

      try {
        // Get last 2 messages for context
        const last2Messages = updatedMessages.slice(-2).map(msg => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.text
        }))

        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: last2Messages
          })
        })

        if (!response.ok) {
          throw new Error('Failed to get response')
        }

        const data = await response.json()

        // Add assistant response with sources and images
        const assistantResponse = {
          id: updatedMessages.length + 1,
          text: data.message || "Sorry, I couldn't process your request.",
          sender: "assistant",
          sources: data.sources || [],
          relatedImages: data.related_images || []
        }

        setMessages(prev => [...prev, assistantResponse])
      } catch (error) {
        console.error('Error getting AI response:', error)

        // Add error message
        const errorResponse = {
          id: updatedMessages.length + 1,
          text: "Sorry, I'm having trouble connecting right now. Please try again.",
          sender: "assistant"
        }

        setMessages(prev => [...prev, errorResponse])
      } finally {
        setIsLoading(false)
      }
    }
  }


  const handleKeyPress = (e: any) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatInlineElements = (text: string) => {
    return text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\)|~~.*?~~)/).map((part, j) => {
      // Bold text **text**
      if (part.startsWith('**') && part.endsWith('**')) {
        return <span key={j} className="font-bold">{part.slice(2, -2)}</span>
      }
      // Italic text *text*
      if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
        return <span key={j} className="italic">{part.slice(1, -1)}</span>
      }
      // Inline code `code`
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={j} className="bg-black/30 text-green-300 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>
      }
      // Links [text](url)
      const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/)
      if (linkMatch) {
        return (
          <a key={j} href={linkMatch[2]} target="_blank" rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 underline">
            {linkMatch[1]}
          </a>
        )
      }
      // Strikethrough ~~text~~
      if (part.startsWith('~~') && part.endsWith('~~')) {
        return <span key={j} className="line-through opacity-70">{part.slice(2, -2)}</span>
      }
      return part
    })
  }


  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button className="gap-2 bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 transition-all duration-300 shadow-lg">
          <MessageCircle size={16} />
          Ask anything
        </Button>
      </SheetTrigger>
      <SheetContent className="flex flex-col h-full bg-background/20 backdrop-blur-3xl border-l border-white/10 shadow-2xl">

        <SheetHeader className="flex-shrink-0 bg-white/5 backdrop-blur-sm border-b border-white/10">
          <SheetTitle className="text-white font-medium text-lg">NASA Space Science Assistant
          </SheetTitle>
          <SheetDescription className="text-white/70 text-sm">
            Ask me anything about NASA space experiments and findings
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className='flex-1 min-h-0'>
          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0 scrollbar-hide">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 backdrop-blur-md transition-all duration-200 ${msg.sender === 'user'
                    ? 'bg-blue-500/80 text-white shadow-lg shadow-blue-500/20'
                    : 'bg-white/10 text-white border border-white/20 shadow-lg'
                    }`}
                >
                  <div className="text-sm leading-relaxed space-y-3">
                    {msg.text.split('\n\n').map((para, i) => {
                      // Handle headers
                      if (para.startsWith('# ')) {
                        return <h1 key={i} className="text-lg font-bold text-white mb-2">{para.slice(2)}</h1>
                      }
                      if (para.startsWith('## ')) {
                        return <h2 key={i} className="text-base font-bold text-white mb-2">{para.slice(3)}</h2>
                      }
                      if (para.startsWith('### ')) {
                        return <h3 key={i} className="text-sm font-bold text-white mb-1">{para.slice(4)}</h3>
                      }

                      // Handle code blocks
                      if (para.startsWith('```')) {
                        const codeContent = para.replace(/```[\w]*\n?/, '').replace(/```$/, '')
                        return (
                          <pre key={i} className="bg-black/30 rounded-lg p-3 overflow-x-auto">
                            <code className="text-xs text-green-300 font-mono">{codeContent}</code>
                          </pre>
                        )
                      }

                      // Handle lists
                      if (para.includes('\n- ') || para.startsWith('- ')) {
                        const listItems = para.split('\n').filter(item => item.trim().startsWith('- '))
                        return (
                          <ul key={i} className="list-disc list-inside space-y-1 text-white/90">
                            {listItems.map((item, idx) => (
                              <li key={idx} className="ml-2">{formatInlineElements(item.slice(2))}</li>
                            ))}
                          </ul>
                        )
                      }

                      // Handle numbered lists
                      if (para.match(/^\d+\. /)) {
                        const listItems = para.split('\n').filter(item => item.match(/^\d+\. /))
                        return (
                          <ol key={i} className="list-decimal list-inside space-y-1 text-white/90">
                            {listItems.map((item, idx) => (
                              <li key={idx} className="ml-2">{formatInlineElements(item.replace(/^\d+\. /, ''))}</li>
                            ))}
                          </ol>
                        )
                      }

                      // Handle blockquotes
                      if (para.startsWith('> ')) {
                        return (
                          <blockquote key={i} className="border-l-4 border-blue-400 pl-4 italic text-white/80 bg-white/5 rounded-r-lg py-2">
                            {formatInlineElements(para.slice(2))}
                          </blockquote>
                        )
                      }

                      // Regular paragraph with inline formatting
                      return (
                        <p key={i} className="text-white/90">
                          {formatInlineElements(para)}
                        </p>
                      )
                    })}

                    {/* Show related images */}
                    {msg.sender === 'assistant' && msg.relatedImages && msg.relatedImages.length > 0 && (
                      <div className="mt-4 space-y-2">
                        <h4 className="text-xs font-semibold text-white/80 mb-2">Related Images:</h4>
                        <div className="grid grid-cols-2 gap-2">
                          {msg.relatedImages.slice(0, 4).map((imageUrl, idx) => (
                            <img
                              key={idx}
                              src={imageUrl}
                              alt={`Related image ${idx + 1}`}
                              className="w-full h-20 object-cover rounded-lg border border-white/20 hover:border-white/40 transition-colors cursor-pointer"
                              onClick={() => window.open(imageUrl, '_blank')}
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none'
                              }}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Show sources */}
                    {msg.sender === 'assistant' && msg.sources && msg.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-white/20">
                        <h4 className="text-xs font-semibold text-white/80 mb-2">Sources:</h4>
                        <div className="space-y-2">
                          {msg.sources.map((source, idx) => (
                            <div key={idx} className="bg-white/5 rounded-lg p-2 border border-white/10">
                              <div className="text-xs text-white/70">
                                <span className="font-medium text-white/90">
                                  {source.metadata?.title || `Source ${idx + 1}`}
                                </span>
                                {source.metadata?.url && (
                                  <a
                                    href={source.metadata.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block text-blue-400 hover:text-blue-300 underline mt-1 truncate"
                                  >
                                    {source.metadata.url}
                                  </a>
                                )}
                                {source.content && (
                                  <p className="mt-1 text-white/60 text-xs line-clamp-2">
                                    {source.content.length > 100
                                      ? source.content.substring(0, 100) + '...'
                                      : source.content
                                    }
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl px-4 py-3 backdrop-blur-md bg-white/10 text-white border border-white/20 shadow-lg">
                  <p className="text-sm leading-relaxed">Thinking...</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Chat Input Area */}
        <SheetFooter className="flex-shrink-0 p-4 bg-white/5 backdrop-blur-sm border-t border-white/10">
          <div className="flex w-full gap-3">
            <div className="flex-1 relative">
              <Input
                placeholder="Type your message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="bg-white/10 backdrop-blur-md border border-white/20 text-white placeholder:text-white/50 rounded-2xl px-4 py-3 focus:bg-white/15 focus:border-white/30 transition-all duration-200 shadow-lg disabled:opacity-50"
              />
            </div>
            <Button
              onClick={handleSendMessage}
              size="sm"
              disabled={isLoading || !message.trim()}
              className="bg-blue-500/80 hover:bg-blue-500 text-white border-0 rounded-2xl px-4 py-3 backdrop-blur-md shadow-lg shadow-blue-500/20 transition-all duration-200 disabled:opacity-50"
            >
              <Send size={16} />
            </Button>
          </div>
          <SheetClose asChild>
            <Button className="mt-3 bg-white/10 hover:bg-white/20 text-white/70 hover:text-white border border-white/20 rounded-2xl backdrop-blur-md transition-all duration-200 shadow-lg">
              <X size={16} className="mr-2" />
              Close Chat
            </Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}