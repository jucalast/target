import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "../components/ui/providers";

export const metadata: Metadata = {
  title: "Target Dashboard",
  description: "Sistema inteligente de análise de dados com Dynamic Island",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-br">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link 
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" 
          rel="stylesheet" 
        />
      </head>
      <body style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'Inter', system-ui, sans-serif" }}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
