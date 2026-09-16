import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/nav/Navbar";
import { PageTransition } from "@/components/PageTransition";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-display",
});
const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "Jobscore: Swipe-based job matching",
  description: "Explainable, mutual-commitment job matching. Swipe right on roles that fit, see exactly why you matched. No black boxes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${inter.variable}`}>
      <body>
        <AuthProvider>
          <Navbar />
          <div className="app-container">
            <PageTransition>{children}</PageTransition>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
