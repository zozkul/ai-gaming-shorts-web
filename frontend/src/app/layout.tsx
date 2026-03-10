import { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Gaming Shorts",
  description: "Turn your long gameplay videos into dynamic, viral shorts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen text-white selection:bg-purple-500/30">
        <div className="premium-bg min-h-screen">
          <div className="relative z-10">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
