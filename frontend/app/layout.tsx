import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ChatProvider, ChatSidebar, ChatToggleButton, MainContent } from "@/components/chat";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Backtesting Research Tool",
  description: "AI-powered trading strategy backtesting platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ChatProvider>
          <MainContent>{children}</MainContent>
          <ChatSidebar />
          <ChatToggleButton />
        </ChatProvider>
      </body>
    </html>
  );
}
