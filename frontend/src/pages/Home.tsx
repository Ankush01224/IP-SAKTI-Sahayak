import React from 'react';
import { useChat } from '../hooks/useChat';
import { ChatWindow } from '../components/ChatWindow';

export const Home: React.FC = () => {
  const {
    messages,
    isLoading,
    language,
    setLanguage,
    error,
    sendMessage,
    clearChat,
  } = useChat();

  return (
    <div className="h-full flex flex-col min-h-0">
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        language={language}
        onSetLanguage={setLanguage}
        onSendMessage={sendMessage}
        onClearChat={clearChat}
        error={error}
      />
    </div>
  );
};
