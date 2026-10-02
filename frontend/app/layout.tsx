import type { Metadata } from 'next';
import { Outfit, Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const outfit = Outfit({ 
  variable: '--font-outfit', 
  subsets: ['latin'], 
  weight: ['500', '600', '700'], 
  display: 'swap' 
});

const inter = Inter({ 
  variable: '--font-inter', 
  subsets: ['latin'], 
  weight: ['400', '500'], 
  display: 'swap' 
});

const mono = JetBrains_Mono({ 
  variable: '--font-mono', 
  subsets: ['latin'], 
  weight: ['400', '500'], 
  display: 'swap' 
});

export const metadata: Metadata = {
  title: 'ArthSaathi — Your Financial Companion',
  description: 'AI-powered financial literacy for gig workers and agricultural laborers in India.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${outfit.variable} ${inter.variable} ${mono.variable} h-full bg-background`} suppressHydrationWarning>
      <body className="h-full flex flex-col antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
