import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

export default function PaymentSuccess() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing'); // processing, success, error
  const [message, setMessage] = useState('Processing your subscription...');
  
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const processSubscription = async () => {
      try {
        // Get subscription ID from URL params
        const subscriptionId = searchParams.get('subscription_id') || 
                              searchParams.get('token') ||
                              searchParams.get('ba_token');
        
        console.log('✅ Payment Success! Subscription ID:', subscriptionId);
        console.log('All URL params:', Object.fromEntries(searchParams));

        if (!subscriptionId) {
          console.error('❌ No subscription ID found in URL');
          setStatus('error');
          setMessage('Could not find subscription information. Redirecting...');
          setTimeout(() => navigate('/dashboard'), 3000);
          return;
        }

        // Update user context with subscription info
        const savedUser = localStorage.getItem('listingspark_user');
        if (savedUser) {
          try {
            const userData = JSON.parse(savedUser);
            userData.subscription = {
              id: subscriptionId,
              plan_type: 'professional',
              status: 'active',
              trial_end: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
              activated_at: new Date().toISOString()
            };
            localStorage.setItem('listingspark_user', JSON.stringify(userData));
            console.log('✅ User context updated with subscription');
          } catch (e) {
            console.error('Failed to update user context:', e);
          }
        }

        // Try to save to backend (best effort)
        const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
        if (token) {
          try {
            await axios.post(
              `${API_URL}/api/subscription/save`,
              {
                subscription_id: subscriptionId,
                plan_type: 'professional',
                status: 'active'
              },
              {
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${token}`
                },
                timeout: 10000
              }
            );
            console.log('✅ Subscription saved to backend');
          } catch (error) {
            console.warn('⚠️ Backend save failed, but subscription is active on PayPal:', error);
          }
        }

        // Show success and redirect
        setStatus('success');
        setMessage('🎉 Subscription activated! Your 3-day trial has started.');
        
        // Redirect after 2 seconds
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 2000);

      } catch (error) {
        console.error('❌ Error processing payment:', error);
        setStatus('error');
        setMessage('Something went wrong. Redirecting to dashboard...');
        setTimeout(() => navigate('/dashboard'), 3000);
      }
    };

    processSubscription();
  }, [searchParams, navigate, API_URL]);

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #6b21a8, #1e3a8a, #4c1d95)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        padding: '40px',
        maxWidth: '500px',
        width: '100%',
        textAlign: 'center',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        color: 'white'
      }}>
        {status === 'processing' && (
          <>
            <div style={{
              width: '80px',
              height: '80px',
              border: '4px solid rgba(168, 85, 247, 0.3)',
              borderTop: '4px solid #a855f7',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 24px'
            }} />
            <style>
              {`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}
            </style>
            <h1 style={{ fontSize: '28px', marginBottom: '16px', fontWeight: 'bold' }}>
              Processing Payment
            </h1>
            <p style={{ fontSize: '18px', opacity: 0.9 }}>
              {message}
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div style={{
              fontSize: '80px',
              marginBottom: '24px',
              animation: 'bounce 1s ease-in-out'
            }}>
              🎉
            </div>
            <style>
              {`
                @keyframes bounce {
                  0%, 100% { transform: translateY(0); }
                  50% { transform: translateY(-20px); }
                }
              `}
            </style>
            <h1 style={{ 
              fontSize: '32px', 
              marginBottom: '16px', 
              fontWeight: 'bold',
              background: 'linear-gradient(to right, #a855f7, #ec4899)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Welcome to ListingSpark Pro!
            </h1>
            <p style={{ fontSize: '18px', opacity: 0.9, marginBottom: '24px' }}>
              {message}
            </p>
            <div style={{
              backgroundColor: 'rgba(34, 197, 94, 0.2)',
              border: '2px solid #22c55e',
              borderRadius: '8px',
              padding: '16px',
              marginTop: '24px'
            }}>
              <p style={{ fontSize: '14px', margin: 0 }}>
                ✅ 3-Day Free Trial Active<br/>
                💳 No charge until trial ends<br/>
                🚀 Redirecting to your dashboard...
              </p>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div style={{ fontSize: '80px', marginBottom: '24px' }}>⚠️</div>
            <h1 style={{ fontSize: '28px', marginBottom: '16px', fontWeight: 'bold' }}>
              Processing Issue
            </h1>
            <p style={{ fontSize: '18px', opacity: 0.9 }}>
              {message}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
