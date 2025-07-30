import type { Metadata } from "next";
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import "./globals.css";
import { Providers } from "../components/ui/providers";

export const metadata: Metadata = {
  title: "Análise de Sentimentos",
  description: "Plataforma para análise de sentimentos de textos",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-br" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="bg-background-dark text-text-primary">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
