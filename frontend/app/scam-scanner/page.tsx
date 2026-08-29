"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { scamApi, ScanInitResponse, ScanStatusResponse } from '@/lib/api/scam';
import { useAuthStore } from '@/store/useAuthStore';

export default function ScamScannerPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<'UPLOAD' | 'VERIFY' | 'ANALYZING' | 'RESULTS'>('UPLOAD');
  const [initResponse, setInitResponse] = useState<ScanInitResponse | null>(null);
  const [verifiedText, setVerifiedText] = useState('');
  const [statusResponse, setStatusResponse] = useState<ScanStatusResponse | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  useEffect(() => {
    if (isMounted && !isAuthenticated) {
      router.push('/login');
    }
  }, [isMounted, isAuthenticated, router]);
  
  // Polling logic
  useEffect(() => {
    let pollInterval: NodeJS.Timeout;
    
    if (step === 'ANALYZING' && initResponse?.document_id) {
      pollInterval = setInterval(async () => {
        try {
          const res = await scamApi.getStatus(initResponse.document_id);
          if (res.status === 'ANALYZED' || res.status === 'FAILED') {
            setStatusResponse(res);
            setStep('RESULTS');
            clearInterval(pollInterval);
          }
        } catch (err: unknown) {
          if (err instanceof Error) {
            setError(err.message || 'Failed to check status');
          } else {
            setError('Failed to check status');
          }
          clearInterval(pollInterval);
        }
      }, 2000); // Poll every 2 seconds
    }
    
    return () => clearInterval(pollInterval);
  }, [step, initResponse]);

  if (!isMounted || !isAuthenticated) {
    return null; // Let the effect redirect
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file first.');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const res = await scamApi.uploadDocument(file);
      setInitResponse(res);
      setVerifiedText(res.extracted_text || '');
      setStep('VERIFY');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to upload document');
      } else {
        setError('Failed to upload document');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!initResponse?.document_id || !verifiedText.trim()) {
      setError('Verified text cannot be empty.');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      await scamApi.verifyDocument(initResponse.document_id, verifiedText);
      setStep('ANALYZING');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to start analysis');
      } else {
        setError('Failed to start analysis');
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  const resetScanner = () => {
    setFile(null);
    setInitResponse(null);
    setVerifiedText('');
    setStatusResponse(null);
    setStep('UPLOAD');
    setError('');
  };

  return (
    <div className="auth-shell">
      <div className="coin-ring"></div>
      
      <div className="auth-card" style={{ maxWidth: '600px' }}>
        <div className="brand-mark">
          <div className="brand-logotype">₹</div>
          <div className="brand-subtitle">Scam Scanner</div>
        </div>
        
        {error && (
          <div className="global-error">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <span>{error}</span>
          </div>
        )}

        {step === 'UPLOAD' && (
          <form onSubmit={handleUpload}>
            <h1 className="auth-heading">Scan a Document</h1>
            <p className="auth-subheading">Upload a loan offer, contract, or scheme document to check for predatory clauses.</p>
            
            <div className="form-group">
              <label htmlFor="document-upload" className="form-label">Document Image (JPEG, PNG, PDF)</label>
              <input 
                id="document-upload"
                type="file" 
                className="form-input" 
                accept="image/jpeg,image/png,application/pdf"
                onChange={handleFileChange}
              />
            </div>
            
            <button type="submit" className="btn-primary" disabled={isLoading || !file}>
              {isLoading ? <div className="btn-spinner"></div> : 'Extract Text'}
            </button>
          </form>
        )}
        
        {step === 'VERIFY' && (
          <form onSubmit={handleVerify}>
            <h1 className="auth-heading">Verify Extracted Text</h1>
            <p className="auth-subheading">Please review and correct the OCR text below before analysis.</p>
            
            <div className="form-group">
              <textarea 
                className="form-input" 
                style={{ minHeight: '200px', resize: 'vertical' }}
                value={verifiedText}
                onChange={(e) => setVerifiedText(e.target.value)}
              />
            </div>
            
            <button type="submit" className="btn-primary" disabled={isLoading}>
              {isLoading ? <div className="btn-spinner"></div> : 'Analyze for Scams'}
            </button>
          </form>
        )}
        
        {step === 'ANALYZING' && (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <h1 className="auth-heading">Analyzing Document...</h1>
            <p className="auth-subheading" style={{ marginBottom: '2rem' }}>ArthSaathi is cross-checking the document against predatory patterns.</p>
            <div className="btn-spinner" style={{ margin: '0 auto', width: '40px', height: '40px', borderWidth: '4px' }}></div>
          </div>
        )}
        
        {step === 'RESULTS' && statusResponse && (
          <div>
            <h1 className="auth-heading">Analysis Results</h1>
            
            {statusResponse.status === 'FAILED' ? (
              <div style={{ marginTop: '1.5rem', padding: '1.5rem', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 68, 68, 0.1)', border: '1px solid var(--color-rose)' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-rose)', marginBottom: '0.5rem' }}>Analysis Failed</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                  {statusResponse.error_message || 'An unexpected error occurred during the analysis. Please check that your LLM provider is running.'}
                </p>
              </div>
            ) : (
              <div style={{ 
                marginTop: '1.5rem', 
                padding: '1.5rem', 
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(0,0,0,0.2)',
                border: `1px solid ${
                  statusResponse.risk_level === 'HIGH' ? 'var(--color-rose)' :
                  statusResponse.risk_level === 'MEDIUM' ? 'var(--color-amber)' : 'rgba(255,255,255,0.1)'
                }`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Risk Level</h2>
                  <span style={{ 
                    padding: '4px 12px', 
                    borderRadius: '99px',
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    background: statusResponse.risk_level === 'HIGH' ? 'rgba(196, 101, 74, 0.2)' : 
                                statusResponse.risk_level === 'MEDIUM' ? 'rgba(232, 168, 56, 0.2)' : 'rgba(255,255,255,0.1)',
                    color: statusResponse.risk_level === 'HIGH' ? 'var(--color-rose)' : 
                           statusResponse.risk_level === 'MEDIUM' ? 'var(--color-amber)' : 'var(--text)'
                  }}>
                    {statusResponse.risk_level}
                  </span>
                </div>
                
                <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                  {statusResponse.risk_summary || 'No risk summary available.'}
                </p>
                
                {statusResponse.matched_clauses && statusResponse.matched_clauses.length > 0 && (
                  <div style={{ marginTop: '1.5rem' }}>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text)', marginBottom: '0.5rem' }}>Matched Patterns:</h3>
                    <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {statusResponse.matched_clauses.map((clause, idx) => (
                        <li key={idx} style={{ marginBottom: '0.5rem' }}>
                          <strong style={{ color: 'var(--color-amber)' }}>{clause.clause_category}</strong>: {clause.explanation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            
            <button onClick={resetScanner} className="btn-primary" style={{ marginTop: '2rem' }}>
              Scan Another Document
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
