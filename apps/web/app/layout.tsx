import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Mosaic — AI investment research",
  description:
    "Ask any SEC filing and get cited, verifiable answers. An AI-powered investment research workspace.",
};

// Runs before first paint: applies the saved theme (default DARK — the intended
// showcase; we deliberately do NOT follow OS preference). Toggling persists to
// localStorage. Inline + blocking so there is no flash of the wrong theme.
const themeScript = `
(function () {
  try {
    var t = localStorage.getItem('theme');
    var d = document.documentElement;
    if (t === 'light') { d.classList.remove('dark'); }
    else { d.classList.add('dark'); }
  } catch (e) { document.documentElement.classList.add('dark'); }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        {children}
      </body>
    </html>
  );
}
