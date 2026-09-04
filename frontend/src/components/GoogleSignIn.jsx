import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

export default function GoogleSignIn({ onLoginSuccess }) {
  const buttonRef = useRef(null);
  const navigate = useNavigate();
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  const handleCredentialResponse = (response) => {
    try {
      // Decode JWT payload safely
      const base64Url = response.credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const user = JSON.parse(jsonPayload);

      localStorage.setItem('auth_token', response.credential);
      localStorage.setItem('user_name', user.name || 'User');
      localStorage.setItem('user_email', user.email || '');

      if (onLoginSuccess) onLoginSuccess(user);
      navigate('/');
    } catch (err) {
      console.error('Failed to parse Google credential token:', err);
    }
  };

  useEffect(() => {
    if (window.google?.accounts?.id && clientId) {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
      });

      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: 'filled_black',
        size: 'large',
        shape: 'pill',
        width: 280,
      });
    }
  }, [clientId]);

  // Demo fallback button if VITE_GOOGLE_CLIENT_ID is not configured
  const handleDemoSignIn = () => {
    localStorage.setItem('auth_token', 'demo_token_authenticated');
    localStorage.setItem('user_name', 'Neo Phukubye');
    localStorage.setItem('user_email', 'demo@smartmoney.momo');
    if (onLoginSuccess) onLoginSuccess({ name: 'Neo Phukubye', email: 'demo@smartmoney.momo' });
    navigate('/');
  };

  return (
    <div className="flex flex-col items-center justify-center gap-2">
      {clientId ? (
        <div ref={buttonRef} />
      ) : (
        <button
          type="button"
          onClick={handleDemoSignIn}
          className="flex items-center justify-center gap-3 w-full max-w-xs bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 text-white font-medium py-2.5 px-4 rounded-full transition shadow-sm"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span className="text-sm">Continue with Google</span>
        </button>
      )}
    </div>
  );
}
