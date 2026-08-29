"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/useAuthStore';

export default function Home() {
  const router = useRouter();
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  useEffect(() => {
    if (isMounted && !isAuthenticated) {
      router.push('/login');
    }
  }, [isMounted, isAuthenticated, router]);
  
  if (!isMounted || !isAuthenticated) {
    return null;
  }

  return (
    <div style={{ minHeight: '100svh', padding: 'var(--sp-8)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-8)' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="brand-mark" style={{ marginBottom: 0, flexDirection: 'row', gap: 'var(--sp-3)' }}>
          <div className="brand-logotype" style={{ fontSize: '1.5rem' }}>₹</div>
          <div className="brand-subtitle">ArthSaathi</div>
        </div>
        
        <div style={{ display: 'flex', gap: 'var(--sp-4)', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Hello, {user?.name}</span>
          <button onClick={clearAuth} style={{ fontSize: '0.875rem', color: 'var(--color-amber)', background: 'none', border: 'none', cursor: 'pointer' }}>Log Out</button>
        </div>
      </header>
      
      <main style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
        <h1 className="auth-heading" style={{ textAlign: 'left', fontSize: '2rem', marginBottom: 'var(--sp-8)' }}>Dashboard</h1>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--sp-6)' }}>
          <Link href="/scam-scanner" style={{ textDecoration: 'none' }}>
            <div className="auth-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', cursor: 'pointer', transition: 'all var(--duration-fast)', padding: 'var(--sp-6)' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-sm)', background: 'rgba(232, 168, 56, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-amber)' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
              </div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text)', margin: 0 }}>Scam Scanner</h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>Scan loan offers, contracts, and scheme documents to detect hidden predatory clauses.</p>
            </div>
          </Link>
          
          {/* Placeholders for future phases */}
          <div className="auth-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', opacity: 0.5, pointerEvents: 'none', padding: 'var(--sp-6)' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text)', margin: 0 }}>Scheme Matchmaker</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>Find the right government schemes based on your profile.</p>
          </div>
          
        </div>
      </main>
    </div>
  );
}
