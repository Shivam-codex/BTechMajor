import "./globals.css";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export const metadata = {
  title: "Smart City Complaint Management System | Non-ML Civic Redressal",
  description: "Academic Final-Year Major Project: Local, Explainable Deterministic NLP & Retrieval-Based Smart City Grievance Redressal.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="flex flex-col min-h-screen antialiased bg-slate-50">
        <Navbar />
        <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
