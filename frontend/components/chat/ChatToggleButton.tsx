'use client';

import { useChatContext } from './ChatProvider';

export function ChatToggleButton() {
  const { isOpen, toggleSidebar, messages } = useChatContext();

  return (
    <button
      onClick={toggleSidebar}
      className={`fixed bottom-6 right-6 z-30 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-200 ${
        isOpen
          ? 'bg-neutral-700 hover:bg-neutral-600'
          : 'bg-gradient-to-br from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500'
      }`}
      title={isOpen ? 'Close chat' : 'Open research agent'}
    >
      {isOpen ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      ) : (
        <>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          {messages.length > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full text-xs flex items-center justify-center text-white font-medium">
              {messages.length > 9 ? '9+' : messages.length}
            </span>
          )}
        </>
      )}
    </button>
  );
}
