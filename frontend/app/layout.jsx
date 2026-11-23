import './globals.css';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';

export const metadata = {
  title: 'AI-Powered ANPR & Traffic Monitoring System',
  description: 'Automated Number Plate Recognition, Vehicle Tracking, and Traffic Analytics Dashboard',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="flex bg-[#0b0f17] text-slate-100 min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Navbar />
          <main className="p-8 flex-1 overflow-y-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
