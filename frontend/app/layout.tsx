import type { Metadata } from "next";
import "./globals.css";
import { ModalProvider } from "./components/ModalContext";

export const metadata: Metadata = {
  title: "Legend Hockey League",
  description: "Historical NHL legends simulation game",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-dark-bg text-dark-text">
        <ModalProvider>
          {children}
        </ModalProvider>
      </body>
    </html>
  );
}
