import type { Metadata } from "next";
import { Inter, Noto_Sans_Devanagari } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const devanagari = Noto_Sans_Devanagari({
  variable: "--font-devanagari",
  subsets: ["devanagari", "latin"],
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ArthSaathi — आर्थसाथी",
  description:
    "आपका वित्तीय साथी। Financial literacy and government scheme guidance for gig and agricultural workers.",
  keywords: ["financial literacy", "gig workers", "government schemes", "Hindi", "ArthSaathi"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="hi"
      className={`${inter.variable} ${devanagari.variable} h-full`}
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}
