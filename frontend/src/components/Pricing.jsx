import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Pricing.css';

const PAYPAL_CLIENT_ID = 'ATYlT9p6S96zZq0t-_SF0CGjwTr29mHE0YyW2TacuJ6QxjnEcznv5TwE6bXhxkEbILf8P5i9rqZz5-SZ';

const pricingTiers = {
  starter: {
    name: "Starter",
    price: 29,
    planId: 'P-9AG34383398031233NDRJZ5I',
    features: [
      "5 Property Listings",
      "Basic Viral Content Generation",
      "Instagram & Facebook Content",
      "Email Support",
      "Basic Analytics"
    ]
  },
  professional: {
    name: "Professional",
    price: 79,
    planId: 'P-3WT18648FL0332636NDRJX2I',
    features: [
      "Unlimited Property Listings",
      "Advanced AI Content Generation",
      "All Social Media Platforms",
      "Virtual Tour Creation",
      "Advanced Analytics",
      "Priority Support",
      "Custom Branding"
    ]
  },
  enterprise: {
    name: "Enterprise",
    price: 149,
    planId: 'P-8N048818NT6287545NDRJVQA',
    features: [
      "Everything in Professional",
      "Multi-Agent Team Access",
      "White-label Solution",
      "API Access",
      "Custom Integrations",
      "Dedicated Account Manager",
      "24/7 Phone Support"
    ]
  }
};

export default function Pricing() {
  const navigate = useNavigate();

  useEffect(() => {
    // Load PayPal SDK
    const script = document.createElement('script');
    script.src = `https://www.paypal.com/sdk/js?client-id=${PAYPAL_CLIENT_ID}&vault=true&intent=subscription`;
    script.async = true;
    script.onload = () => {
      // Initialize all PayPal buttons after SDK loads
      initializePayPalButtons();
    };
    document.body.appendChild(script);

    return () => {
      // Cleanup script on unmount
      const scripts = document.querySelectorAll(`script[src*="paypal.com/sdk"]`);
      scripts.forEach(s => s.remove());
    };
  }, []);

  const initializePayPalButtons = () => {
    Object.entries(pricingTiers).forEach(([key, tier]) => {
      const containerId = `paypal-button-${key}`;
      const container = document.getElementById(containerId);
      
      if (container && window.paypal) {
        // Clear existing buttons
        container.innerHTML = '';
        
        window.paypal.Buttons({
          style: {
            shape: 'rect',
            color: 'blue',
            layout: 'vertical',
            label: 'subscribe'
          },
          createSubscription: function(data, actions) {
            return actions.subscription.create({
              plan_id: tier.planId
            });
          },
          onApprove: function(data, actions) {
            // Save subscription ID to backend
            saveSubscription(data.subscriptionID, key);
            
            // Redirect to dashboard
            navigate('/dashboard', { 
              state: { 
                message: 'Subscription activated successfully!',
                subscriptionId: data.subscriptionID,
                plan: key
              }
            });
          },
          onError: function(err) {
            console.error('PayPal error:', err);
            alert('Payment failed. Please try again.');
          },
          onCancel: function(data) {
            console.log('Payment cancelled:', data);
          }
        }).render(`#${containerId}`);
      }
    });
  };

  const saveSubscription = async (subscriptionId, planType) => {
    try {
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');
      
      await fetch(`${API_URL}/api/subscription/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subscription_id: subscriptionId,
          plan_type: planType,
          status: 'active'
        })
      });
    } catch (error) {
      console.error('Error saving subscription:', error);
    }
  };

  return (
    <div className="pricing-container">
      <h1>Choose Your Plan</h1>
      <p className="pricing-subtitle">Start your free trial today - cancel anytime</p>
      
      <div className="pricing-grid">
        {Object.entries(pricingTiers).map(([key, tier]) => (
          <div key={key} className={`pricing-card ${key === 'professional' ? 'popular' : ''}`}>
            {key === 'professional' && <div className="popular-badge">Most Popular</div>}
            
            <h2>{tier.name}</h2>
            <div className="price">
              <span className="currency">$</span>
              <span className="amount">{tier.price}</span>
              <span className="period">/month</span>
            </div>
            
            <ul className="features">
              {tier.features.map((feature, idx) => (
                <li key={idx}>
                  <span className="checkmark">✓</span> {feature}
                </li>
              ))}
            </ul>
            
            {/* PayPal Button Container */}
            <div id={`paypal-button-${key}`} className="paypal-button-wrapper"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
