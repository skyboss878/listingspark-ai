import { useEffect, useCallback, useState, useRef } from 'react';

import axios from '../api';
import './Pricing.css';

export default function Pricing() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sdkLoading, setSdkLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState(null);
  const buttonInitialized = useRef(false);
  const scriptLoaded = useRef(false);
  const redirectTimerRef = useRef(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  const PLAN_ID = 'P-1N875595TN640074WNDTXDAQ';
  const PAYPAL_CLIENT_ID = 'ATYlT9p6S96zZq0t-_SF0CGjwTr29mHE0YyW2TacuJ6QxjnEcznv5TwE6bXhxkEbILf8P5i9rqZz5-SZ';

  const saveSubscription = useCallback(async (subscriptionId) => {
    const token = localStorage.getItem('token');
    const authToken = localStorage.getItem('auth_token');
    const actualToken = token || authToken;

    if (!actualToken) {
      console.warn('⚠️ No auth token found, subscription saved on PayPal only');
      return { success: true, subscription_id: subscriptionId };
    }

    try {
      console.log('💾 Saving subscription:', subscriptionId);

      const response = await axios.post(
        `${API_URL}/api/subscription/save`,
        {
          subscription_id: subscriptionId,
          plan_type: 'professional',
          status: 'active'
        },
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${actualToken}`
          },
          timeout: 15000
        }
      );

      console.log('✅ Subscription saved successfully:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Save subscription error:', error);
      console.warn('⚠️ Backend save failed but subscription is active on PayPal');
      return { success: true, subscription_id: subscriptionId };
    }
  }, [API_URL]);

  const initializePayPalButton = useCallback(() => {
    console.log('🔄 Initializing PayPal button...');

    if (buttonInitialized.current) {
      console.log('⚠️ Button already initialized, skipping...');
      return;
    }

    if (!window.paypal) {
      console.error('❌ PayPal SDK not loaded!');
      setError('PayPal SDK failed to load. Please refresh the page.');
      return;
    }

    buttonInitialized.current = true;
    setSdkLoading(false);

    const container = document.getElementById('paypal-button-container');
    if (!container) {
      console.error('❌ Container not found');
      return;
    }

    console.log('✅ Rendering PayPal button');
    container.innerHTML = '';

    window.paypal.Buttons({
      style: {
        shape: 'rect',
        color: 'blue',
        layout: 'vertical',
        label: 'subscribe'
      },
      createSubscription: (data, actions) => {
        console.log('📝 Creating subscription');
        setLoading(true);
        setError(null);

        return actions.subscription.create({
          plan_id: PLAN_ID,
          application_context: {
            brand_name: "ListingSpark Pro",
            shipping_preference: "NO_SHIPPING",
            user_action: "SUBSCRIBE_NOW"
          }
        });
      },
      onApprove: async (data) => {
        console.log('✅ PayPal approved:', data);
        setLoading(true);

        try {
          // Save subscription to backend (best effort)
          await saveSubscription(data.subscriptionID);

          // Update user context with subscription info
          const savedUser = localStorage.getItem('listingspark_user');
          if (savedUser) {
            try {
              const userData = JSON.parse(savedUser);
              userData.subscription = {
                id: data.subscriptionID,
                plan_type: 'professional',
                status: 'active',
                trial_end: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
              };
              localStorage.setItem('listingspark_user', JSON.stringify(userData));
              console.log('✅ User context updated with subscription');
            } catch (e) {
              console.error('Failed to update user context:', e);
            }
          }

          // Show success message
          setSuccessMessage('🎉 Subscription activated! Redirecting to dashboard...');

          // Use a ref to track the timer so it won't be cleared on unmount
          console.log('🔄 Starting redirect timer...');
          redirectTimerRef.current = setTimeout(() => {
            console.log('🔄 Redirecting to dashboard NOW...');
            window.location.href = '/dashboard';
          }, 1500);

        } catch (err) {
          console.error('❌ Error processing subscription:', err);

          // Still redirect since PayPal subscription is active
          setSuccessMessage(
            `✅ Subscription activated! (ID: ${data.subscriptionID})\n` +
            'Redirecting to dashboard...'
          );

          redirectTimerRef.current = setTimeout(() => {
            console.log('🔄 Redirecting to dashboard after error...');
            window.location.href = '/dashboard';
          }, 1500);
        }
      },
      onError: (err) => {
        console.error('❌ PayPal error:', err);
        setError('Payment processing failed. Please try again or contact support.');
        setLoading(false);
      },
      onCancel: () => {
        console.log('⚠️ Payment cancelled by user');
        setLoading(false);
        setError(null);
      }
    }).render('#paypal-button-container')
      .then(() => console.log('✅ Button rendered successfully'))
      .catch(err => {
        console.error('❌ Button render failed:', err);
        setError('Failed to load payment button. Please refresh the page.');
        buttonInitialized.current = false;
      });
  }, [saveSubscription, PLAN_ID]);

  useEffect(() => {
    console.log('🚀 Pricing component mounted');

    const existingScript = document.querySelector('script[src*="paypal.com/sdk"]');

    if (existingScript && window.paypal) {
      console.log('✅ PayPal SDK already loaded');
      if (!buttonInitialized.current) {
        setTimeout(initializePayPalButton, 100);
      }
      return;
    }

    if (scriptLoaded.current) {
      console.log('⚠️ Script already loading');
      return;
    }

    scriptLoaded.current = true;
    console.log('📦 Loading PayPal SDK...');

    const script = document.createElement('script');
    script.src = `https://www.paypal.com/sdk/js?client-id=${PAYPAL_CLIENT_ID}&vault=true&intent=subscription`;
    script.async = true;

    script.onload = () => {
      console.log('✅ PayPal SDK loaded');
      setTimeout(initializePayPalButton, 500);
    };

    script.onerror = (e) => {
      console.error('❌ PayPal SDK load failed:', e);
      setError('Failed to load PayPal. Please check your connection and refresh.');
      setSdkLoading(false);
      scriptLoaded.current = false;
    };

    document.body.appendChild(script);

    return () => {
      console.log('🧹 Component cleanup');
      // Clear any pending redirect timers
      if (redirectTimerRef.current) {
        clearTimeout(redirectTimerRef.current);
      }
      buttonInitialized.current = false;
    };
  }, [PAYPAL_CLIENT_ID, initializePayPalButton]);

  return (
    <div className="pricing-container">
      <h1>Start Your Free Trial</h1>
      <p className="pricing-subtitle">3-day free trial, then $129/month - cancel anytime</p>

      {successMessage && (
        <div style={{
          backgroundColor: '#d4edda',
          border: '2px solid #c3e6cb',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '30px',
          color: '#155724',
          maxWidth: '600px',
          margin: '0 auto 30px',
          textAlign: 'center',
          fontSize: '1.1rem',
          fontWeight: '600',
          whiteSpace: 'pre-line'
        }}>
          {successMessage}
        </div>
      )}

      {error && (
        <div style={{
          backgroundColor: '#fee',
          border: '2px solid #fcc',
          borderRadius: '8px',
          padding: '16px 20px',
          marginBottom: '30px',
          color: '#c00',
          maxWidth: '600px',
          margin: '0 auto 30px'
        }}>
          <strong>⚠ Error:</strong> {error}
        </div>
      )}

      {sdkLoading && !error && !successMessage && (
        <div style={{
          textAlign: 'center',
          padding: '20px',
          color: '#fff',
          fontSize: '1.1rem'
        }}>
          Loading payment options...
        </div>
      )}

      <div className="pricing-single">
        <div className="pricing-card professional">
          <div className="popular-badge">Professional Plan</div>
          <h2>All-In-One Real Estate Marketing</h2>
          <div className="price">
            <span className="currency">$</span>
            <span className="amount">129</span>
            <span className="period">/month</span>
          </div>

          <div className="trial-notice">
            🎉 <strong>3-Day Free Trial</strong> - No charge until trial ends
          </div>

          <ul className="features">
            <li><span className="checkmark">✓</span> Unlimited Property Listings</li>
            <li><span className="checkmark">✓</span> AI-Powered Content Generation</li>
            <li><span className="checkmark">✓</span> 360° Virtual Tours</li>
            <li><span className="checkmark">✓</span> Instagram & Facebook Content</li>
            <li><span className="checkmark">✓</span> Advanced Analytics Dashboard</li>
            <li><span className="checkmark">✓</span> Email & Priority Support</li>
            <li><span className="checkmark">✓</span> Custom Branding Options</li>
            <li><span className="checkmark">✓</span> MLS Integration (Coming Soon)</li>
          </ul>

          <div
            id="paypal-button-container"
            className="paypal-button-wrapper"
            style={{
              opacity: (loading || successMessage) ? 0.6 : 1,
              minHeight: '50px',
              transition: 'opacity 0.3s',
              pointerEvents: (loading || successMessage) ? 'none' : 'auto'
            }}
          />

          {loading && !successMessage && (
            <div style={{
              textAlign: 'center',
              marginTop: '10px',
              color: '#666',
              fontStyle: 'italic'
            }}>
              Processing payment...
            </div>
          )}

          <p className="terms-notice">
            By subscribing, you agree to our <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a>
          </p>
        </div>
      </div>
    </div>
  );
}
